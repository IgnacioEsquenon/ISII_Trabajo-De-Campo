from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, Especialidad, BloqueHorario, Turno, Reserva
)


class TestTurno(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico9', password='1234')
        medico       = Medico.objects.create(
            user=user, nombre='García', matricula='M009',
            especialidad=especialidad, estado='aprobado'
        )
        bloque       = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        self.turno   = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )

    def test_bloquear(self):
        """bloquear() pone esta_reservado en True."""
        self.turno.bloquear()
        self.turno.refresh_from_db()
        self.assertTrue(self.turno.esta_reservado)

    def test_liberar(self):
        """liberar() pone esta_reservado en False."""
        self.turno.bloquear()
        self.turno.liberar()
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_reservado)

    def test_desactivar(self):
        """desactivar() pone esta_activo en False."""
        self.turno.desactivar()
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_activo)

    def test_esta_disponible_turno_libre(self):
        """esta_disponible() devuelve True si no está reservado ni inactivo."""
        self.assertTrue(self.turno.esta_disponible())

    def test_esta_disponible_turno_reservado(self):
        """esta_disponible() devuelve False si está reservado."""
        self.turno.bloquear()
        self.assertFalse(self.turno.esta_disponible())

    def test_esta_disponible_turno_inactivo(self):
        """esta_disponible() devuelve False si está inactivo."""
        self.turno.desactivar()
        self.assertFalse(self.turno.esta_disponible())


class TestBloqueHorario(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico10', password='1234')
        medico       = Medico.objects.create(
            user=user, nombre='García', matricula='M010',
            especialidad=especialidad, estado='aprobado'
        )
        self.bloque  = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )

    def test_desactivar(self):
        """desactivar() pone activo en False."""
        self.bloque.desactivar()
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)

    def test_obtener_turnos_disponibles(self):
        """obtener_turnos_disponibles devuelve solo turnos disponibles futuros."""
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,30), hora_fin=time(10,0),
            esta_reservado=True, esta_activo=True
        )
        resultado = self.bloque.obtener_turnos_disponibles()
        self.assertEqual(resultado.count(), 1)


class TestMedico(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico11', password='1234')
        self.medico  = Medico.objects.create(
            user=user, nombre='García', matricula='M011',
            especialidad=especialidad, estado='pendiente'
        )

    def test_aprobar(self):
        """aprobar() cambia estado a aprobado."""
        self.medico.aprobar()
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.estado, 'aprobado')

    def test_rechazar(self):
        """rechazar() cambia estado a rechazado."""
        self.medico.rechazar()
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.estado, 'rechazado')

    def test_esta_aprobado_true(self):
        """esta_aprobado() devuelve True cuando estado es aprobado."""
        self.medico.aprobar()
        self.assertTrue(self.medico.esta_aprobado())

    def test_esta_aprobado_false(self):
        """esta_aprobado() devuelve False cuando estado es pendiente."""
        self.assertFalse(self.medico.esta_aprobado())

    def test_existe_por_matricula_true(self):
        """existe_por_matricula devuelve True si la matrícula existe."""
        self.assertTrue(Medico.existe_por_matricula('M011'))

    def test_existe_por_matricula_false(self):
        """existe_por_matricula devuelve False si la matrícula no existe."""
        self.assertFalse(Medico.existe_por_matricula('ZZZZ'))


class TestReservaModelo(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user_med     = User.objects.create_user(username='medico12', password='1234')
        medico       = Medico.objects.create(
            user=user_med, nombre='García', matricula='M012',
            especialidad=especialidad, estado='aprobado'
        )
        bloque       = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        self.turno   = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=2),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        user_pac     = User.objects.create_user(username='paciente5', password='1234')
        paciente     = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='55555555'
        )
        self.reserva = Reserva.objects.create(
            turno=self.turno, paciente=paciente
        )

    def test_cancelar(self):
        """cancelar() cambia estado a cancelada y libera el turno."""
        self.reserva.cancelar()
        self.reserva.refresh_from_db()
        self.turno.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'cancelada')
        self.assertFalse(self.turno.esta_reservado)

    def test_horas_hasta_el_turno(self):
        """horas_hasta_el_turno devuelve un valor positivo para turnos futuros."""
        resultado = self.reserva.horas_hasta_el_turno()
        self.assertGreater(resultado, 0)

    def test_codigo_reserva_generado(self):
        """El código de reserva se genera automáticamente."""
        self.assertTrue(self.reserva.codigo_reserva.startswith('RES-'))

    def test_codigo_reserva_unico(self):
        """Dos reservas no pueden tener el mismo código."""
        user_pac2    = User.objects.create_user(username='paciente6', password='1234')
        paciente2    = Paciente.objects.create(
            user=user_pac2, nombre='Ana', apellido='Gomez', dni='66666666'
        )
        turno2       = Turno.objects.create(
            bloque=self.turno.bloque,
            fecha=date.today() + timedelta(days=3),
            hora_inicio=time(9,30), hora_fin=time(10,0),
            esta_reservado=True, esta_activo=True
        )
        reserva2     = Reserva.objects.create(
            turno=turno2, paciente=paciente2
        )
        self.assertNotEqual(
            self.reserva.codigo_reserva,
            reserva2.codigo_reserva
        )
    
    def test_horas_hasta_el_turno_pasado_devuelve_cero_o_negativo(self):
        """horas_hasta_el_turno debe manejar correctamente fechas pasadas sin romper la app."""
        from django.utils import timezone
        
        # Simulamos que el turno fue hace 2 días
        pasado = timezone.now() - timedelta(days=2)
        self.turno.fecha = pasado.date()
        self.turno.hora_inicio = pasado.time()
        self.turno.save()

        resultado = self.reserva.horas_hasta_el_turno()
        
        # Dependiendo de tu lógica en el modelo, debería devolver 0 o un número negativo.
        # Aseguramos que sea menor o igual a cero (nunca positivo).
        self.assertLessEqual(resultado, 0)