from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import Medico, BloqueHorario, Turno, Especialidad, Reserva, Paciente
from gestion_turnos.servicios.gestor_agenda import GestorAgenda


class TestGestorAgendaCrearBloque(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user          = User.objects.create_user(username='medico1', password='1234')
        self.medico   = Medico.objects.create(
            user=user, nombre='García', matricula='M001',
            especialidad=especialidad, estado='aprobado'
        )
        self.gestor = GestorAgenda(self.medico)

    def test_CP01_creacion_exitosa(self):
        """CP-01: Bloque válido sin superposición genera turnos correctamente."""
        bloque = self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(10,0), duracion_turno=30
        )
        self.assertIsNotNone(bloque.pk)
        self.assertTrue(Turno.objects.filter(bloque=bloque).exists())

    def test_CP02_hora_fin_menor_a_inicio(self):
        """CP-02: Hora fin menor a hora inicio lanza ValidationError."""
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0, hora_inicio=time(10,0),
                hora_fin=time(9,0), duracion_turno=30
            )

    def test_CP03_duracion_mayor_al_bloque(self):
        """CP-03: Duración de turno mayor al bloque lanza ValidationError."""
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0, hora_inicio=time(9,0),
                hora_fin=time(9,20), duracion_turno=30
            )

    def test_CP04_superposicion_con_bloque_existente(self):
        """CP-04: Bloque superpuesto con uno existente lanza ValidationError."""
        self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(10,0), duracion_turno=30
        )
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0, hora_inicio=time(9,30),
                hora_fin=time(10,30), duracion_turno=30
            )

    def test_CP05_bloque_exactamente_del_tamanio_de_un_turno(self):
        """CP-05: Bloque de 30 min con turnos de 30 min genera 1 turno por semana."""
        bloque = self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(9,30), duracion_turno=30
        )
        self.assertEqual(Turno.objects.filter(bloque=bloque).count(), 4)

    def test_CP06_genera_8_turnos_para_4_semanas(self):
        """CP-06: Bloque de 1 hora con turnos de 30 min genera 8 turnos totales."""
        bloque = self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(10,0), duracion_turno=30
        )
        self.assertEqual(Turno.objects.filter(bloque=bloque).count(), 8)

    def test_CP07_no_genera_turnos_en_franjas_reservadas(self):
        """CP-07: Al editar, no genera turno en franja ya reservada."""
        # Creamos un bloque inicial
        bloque = self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(10,0), duracion_turno=30
        )
        # Tomamos el primer turno y lo reservamos correctamente
        turno = Turno.objects.filter(bloque=bloque).first()
        turno.bloquear()  # ← simula la acción del GestorReserva

        # Creamos un paciente con un usuario propio (no el del médico)
        paciente_user = User.objects.create_user(username='paciente_test', password='1234')
        paciente = Paciente.objects.create(
            user=paciente_user, nombre='Paciente', apellido='Test', dni='12345678'
        )
        Reserva.objects.create(turno=turno, paciente=paciente)

        # Editamos el bloque (internamente elimina el viejo y crea uno nuevo)
        self.gestor.editar_bloque_horario(
            bloque=bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )

        # Verificar que en el nuevo bloque no se duplicó el turno reservado
        duplicados = Turno.objects.filter(
            bloque__medico=self.medico,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            esta_reservado=True
        ).count()
        self.assertEqual(duplicados, 1)

    def test_CP08_hora_fin_igual_a_inicio(self):
        """CP-08: Hora fin exactamente igual a hora inicio lanza ValidationError."""
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0,
                hora_inicio=time(9,0),
                hora_fin=time(9,0),
                duracion_turno=30
            )


class TestGestorAgendaEliminarBloque(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user          = User.objects.create_user(username='medico2', password='1234')
        self.medico   = Medico.objects.create(
            user=user, nombre='García', matricula='M002',
            especialidad=especialidad, estado='aprobado'
        )
        self.gestor = GestorAgenda(self.medico)
        self.bloque = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )

    def test_CP09_eliminar_bloque_se_desactiva(self):
        """CP-09: Bloque sin turnos reservados se desactiva correctamente."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.gestor.eliminar_bloque_horario(self.bloque)
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)

    def test_CP10_eliminar_bloque_desactiva_turnos(self):
        """CP-10: Al eliminar el bloque se desactivan sus turnos."""
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.gestor.eliminar_bloque_horario(self.bloque)
        turno.refresh_from_db()
        self.assertFalse(turno.esta_activo)

    def test_CP11_eliminar_bloque_mantiene_reservas(self):
        """CP-11: Al eliminar el bloque los turnos reservados se desactivan pero no se borran."""
        paciente = Paciente.objects.create(
            user=self.medico.user, nombre='Paciente', apellido='Test', dni='11111111'
        )
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        Reserva.objects.create(turno=turno, paciente=paciente)
        self.gestor.eliminar_bloque_horario(self.bloque)
        turno.refresh_from_db()
        # El turno se desactiva pero sigue existiendo y sigue reservado
        self.assertFalse(turno.esta_activo)
        self.assertTrue(turno.esta_reservado)

    def test_CP12_eliminar_bloque_con_reservados_no_lanza_error(self):
        """CP-12: Bloque con turnos reservados se elimina sin errores (diseño final)."""
        paciente = Paciente.objects.create(
            user=self.medico.user, nombre='Paciente', apellido='Test', dni='22222222'
        )
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        Reserva.objects.create(turno=turno, paciente=paciente)
        # No debe lanzar error
        self.gestor.eliminar_bloque_horario(self.bloque)
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)


class TestGestorAgendaEditarBloque(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user          = User.objects.create_user(username='medico3', password='1234')
        self.medico   = Medico.objects.create(
            user=user, nombre='García', matricula='M003',
            especialidad=especialidad, estado='aprobado'
        )
        self.gestor = GestorAgenda(self.medico)
        self.bloque = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )

    def test_CP13_editar_bloque_crea_nuevo_bloque(self):
        """CP-13: Editar bloque desactiva el original y crea uno nuevo."""
        nuevo = self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=60
        )
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)          # original desactivado
        self.assertTrue(nuevo.activo)                 # nuevo activo
        self.assertNotEqual(self.bloque.pk, nuevo.pk) # son distintos

    def test_CP14_editar_bloque_regenera_turnos(self):
        """CP-14: Al editar, el nuevo bloque genera turnos correctamente."""
        self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )
        # El nuevo bloque debe tener 4 turnos/semana * 4 semanas = 16 turnos libres
        nuevo_bloque = BloqueHorario.objects.filter(medico=self.medico, activo=True).first()
        self.assertEqual(
            Turno.objects.filter(bloque=nuevo_bloque, esta_reservado=False).count(), 16
        )

    def test_CP15_editar_bloque_respeta_turnos_reservados(self):
        """CP-15: Al editar no se regenera turno en franja ya reservada."""
        paciente = Paciente.objects.create(
            user=self.medico.user, nombre='Paciente', apellido='Test', dni='33333333'
        )
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        Reserva.objects.create(turno=turno, paciente=paciente)
        self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )
        # Buscar turnos reservados en esa franja para este médico
        duplicados = Turno.objects.filter(
            bloque__medico=self.medico,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            esta_reservado=True
        ).count()
        self.assertEqual(duplicados, 1)


class TestGestorAgendaObtener(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user          = User.objects.create_user(username='medico4', password='1234')
        self.medico   = Medico.objects.create(
            user=user, nombre='García', matricula='M004',
            especialidad=especialidad, estado='aprobado'
        )
        self.gestor = GestorAgenda(self.medico)

    def test_CP16_obtener_estructura_bloques_agrupa_por_dia(self):
        """CP-16: obtener_estructura_bloques devuelve dict agrupado por día."""
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )
        resultado = self.gestor.obtener_estructura_bloques()
        self.assertIn('Lunes', resultado)

    def test_CP17_obtener_estructura_bloques_no_incluye_inactivos(self):
        """CP-17: obtener_estructura_bloques no incluye bloques desactivados."""
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=False
        )
        resultado = self.gestor.obtener_estructura_bloques()
        self.assertEqual(len(resultado), 0)