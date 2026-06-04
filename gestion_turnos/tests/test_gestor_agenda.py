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
        """CP-07: No genera turno disponible en franja ya reservada."""
        bloque = self.gestor.crear_bloque_horario(
            dia_semana=0, hora_inicio=time(9,0),
            hora_fin=time(10,0), duracion_turno=30
        )
        # Reserva un turno manualmente
        turno = Turno.objects.filter(bloque=bloque).first()
        turno.bloquear()

        # Edita el bloque — no debe duplicar el turno reservado
        self.gestor.editar_bloque_horario(
            bloque=bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )

        duplicados = Turno.objects.filter(
            bloque=bloque, fecha=turno.fecha, hora_inicio=turno.hora_inicio
        ).count()
        self.assertEqual(duplicados, 1)

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

    def test_eliminar_bloque_sin_reservados(self):
        """Bloque sin turnos reservados se desactiva correctamente."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.gestor.eliminar_bloque_horario(self.bloque)
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)

    def test_eliminar_bloque_borra_turnos_disponibles(self):
        """Al eliminar el bloque se borran los turnos disponibles futuros."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.gestor.eliminar_bloque_horario(self.bloque)
        self.assertEqual(
            Turno.objects.filter(bloque=self.bloque, esta_reservado=False).count(), 0
        )

    def test_eliminar_bloque_con_reservados_lanza_error(self):
        """Bloque con turnos reservados activos no puede eliminarse."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        with self.assertRaises(ValidationError):
            self.gestor.eliminar_bloque_horario(self.bloque)

    def test_eliminar_bloque_mantiene_turnos_reservados(self):
        """Al eliminar el bloque los turnos reservados no se borran."""
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        # No puede eliminarse, pero verificamos que el turno sigue
        try:
            self.gestor.eliminar_bloque_horario(self.bloque)
        except ValidationError:
            pass
        self.assertTrue(Turno.objects.filter(pk=turno.pk).exists())


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

    def test_editar_bloque_actualiza_datos(self):
        """Editar bloque cambia sus atributos correctamente."""
        self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=60
        )
        self.bloque.refresh_from_db()
        self.assertEqual(self.bloque.hora_fin, time(11,0))
        self.assertEqual(self.bloque.duracion_turno, 60)

    def test_editar_bloque_borra_disponibles_y_regenera(self):
        """Al editar se borran los disponibles y se regeneran nuevos."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )
        # Con 2hs y turnos de 30 min son 4 turnos por semana x 4 semanas
        self.assertEqual(
            Turno.objects.filter(bloque=self.bloque, esta_reservado=False).count(), 16
        )

    def test_editar_bloque_respeta_turnos_reservados(self):
        """Al editar no se regenera turno en franja ya reservada."""
        turno = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        self.gestor.editar_bloque_horario(
            bloque=self.bloque, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(11,0), duracion_turno=30
        )
        duplicados = Turno.objects.filter(
            bloque=self.bloque,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio
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

    def test_obtener_estructura_bloques_agrupa_por_dia(self):
        """obtener_estructura_bloques devuelve dict agrupado por día."""
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )
        resultado = self.gestor.obtener_estructura_bloques()
        self.assertIn('Lunes', resultado)

    def test_obtener_estructura_bloques_no_incluye_inactivos(self):
        """obtener_estructura_bloques no incluye bloques desactivados."""
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=False
        )
        resultado = self.gestor.obtener_estructura_bloques()
        self.assertEqual(len(resultado), 0)

    def test_obtener_bloques_devuelve_solo_activos(self):
        """obtener_bloques devuelve solo bloques con activo=True."""
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )
        BloqueHorario.objects.create(
            medico=self.medico, dia_semana=1,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=False
        )
        self.assertEqual(self.gestor.obtener_bloques().count(), 1)
    
    def test_CP18_hora_fin_igual_a_inicio(self):
        """CP-18: Hora fin exactamente igual a hora inicio lanza ValidationError."""
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0, 
                hora_inicio=time(9,0),
                hora_fin=time(9,0), # Duración cero
                duracion_turno=30
            )

    def test_CP19_cruce_de_medianoche(self):
        """CP-19: Bloque que cruza la medianoche lanza ValidationError."""
        # Un turno que empieza a las 23:00 y termina a las 02:00 del día siguiente.
        # El sistema debería exigir que se parta en dos bloques distintos por día.
        with self.assertRaises(ValidationError):
            self.gestor.crear_bloque_horario(
                dia_semana=0, 
                hora_inicio=time(23,0),
                hora_fin=time(2,0), 
                duracion_turno=30
            )