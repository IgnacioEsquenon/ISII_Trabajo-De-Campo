from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, BloqueHorario, Turno, Reserva, Especialidad
)
from gestion_turnos.servicios.gestor_reserva import GestorReserva


class TestGestorReservaReservarTurno(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user_med      = User.objects.create_user(username='medico1', password='1234')
        self.medico   = Medico.objects.create(
            user=user_med, nombre='García', matricula='M001',
            especialidad=especialidad, estado='aprobado'
        )
        self.bloque   = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        self.turno    = Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        user_pac      = User.objects.create_user(username='paciente1', password='1234')
        self.paciente = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='12345678'
        )
        self.gestor   = GestorReserva()

    def test_CP08_reserva_exitosa(self):
        """CP-08: Turno disponible y paciente válido crea la reserva."""
        reserva = self.gestor.reservar_turno(self.paciente, self.turno)
        self.assertIsNotNone(reserva.pk)
        self.assertEqual(reserva.paciente, self.paciente)

    def test_CP09_turno_ya_reservado_lanza_error(self):
        """CP-09: Intentar reservar un turno ya reservado lanza ValidationError."""
        self.turno.bloquear()
        with self.assertRaises(ValidationError):
            self.gestor.reservar_turno(self.paciente, self.turno)

    def test_CP10_codigo_reserva_generado(self):
        """CP-10: La reserva tiene un código único que empieza con RES-."""
        reserva = self.gestor.reservar_turno(self.paciente, self.turno)
        self.assertTrue(reserva.codigo_reserva.startswith('RES-'))

    def test_CP11_turno_pasa_a_reservado(self):
        """CP-11: Después de reservar el turno queda bloqueado."""
        self.gestor.reservar_turno(self.paciente, self.turno)
        self.turno.refresh_from_db()
        self.assertTrue(self.turno.esta_reservado)

    def test_CP12_turno_inactivo_no_reservable(self):
        """CP-12: Turno inactivo no puede reservarse."""
        self.turno.desactivar()
        with self.assertRaises(ValidationError):
            self.gestor.reservar_turno(self.paciente, self.turno)

class TestGestorReservaCancelar(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user_med      = User.objects.create_user(username='medico5', password='1234')
        medico        = Medico.objects.create(
            user=user_med, nombre='García', matricula='M005',
            especialidad=especialidad, estado='aprobado'
        )
        bloque        = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        self.turno    = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=2),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        user_pac      = User.objects.create_user(username='paciente2', password='1234')
        paciente      = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='11111111'
        )
        self.reserva  = Reserva.objects.create(
            turno=self.turno, paciente=paciente
        )
        self.gestor   = GestorReserva()

    def test_cancelar_reserva_exitosa(self):
        """Cancelar reserva con más de 24hs cambia estado a cancelada."""
        self.gestor.cancelar_reserva(self.reserva)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'cancelada')

    def test_cancelar_reserva_libera_turno(self):
        """Cancelar reserva libera el turno."""
        self.gestor.cancelar_reserva(self.reserva)
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_reservado)

    def test_cancelar_reserva_menos_24hs_lanza_error(self):
        """Cancelar reserva con menos de 24hs lanza ValidationError."""
        from django.utils import timezone
        ahora = timezone.now() + timedelta(hours=12)
        self.turno.fecha       = ahora.date()
        self.turno.hora_inicio = ahora.time()
        self.turno.save()
        with self.assertRaises(ValidationError):
            self.gestor.cancelar_reserva(self.reserva)