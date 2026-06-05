from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta, datetime
from django.utils import timezone
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, BloqueHorario, Turno, Reserva, Especialidad
)

class TestReservaEsCancelable(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user_med      = User.objects.create_user(username='medico1', password='1234')
        medico        = Medico.objects.create(
            user=user_med, nombre='García', matricula='M001',
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
        user_pac      = User.objects.create_user(username='paciente1', password='1234')
        paciente      = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='12345678'
        )
        self.reserva  = Reserva.objects.create(
            turno=self.turno, paciente=paciente
        )

    def test_cancelable_con_mas_de_24hs(self):
        """CP-13: Reserva con turno en 48hs es cancelable."""
        self.turno.fecha = date.today() + timedelta(days=2)
        self.turno.hora_inicio = time(9, 0)
        self.turno.save()
        self.assertTrue(self.reserva.es_cancelable())

    def test_no_cancelable_con_menos_de_24hs(self):
        """CP-14: Reserva con turno en 12hs no es cancelable."""
        ahora = timezone.now() + timedelta(hours=12)
        self.turno.fecha       = ahora.date()
        self.turno.hora_inicio = ahora.time()
        self.turno.save()
        self.assertFalse(self.reserva.es_cancelable())

    def test_caso_borde_exactamente_24hs(self):
        """CP-15: Exactamente 24hs antes no es cancelable."""
        ahora = timezone.now() + timedelta(hours=24)
        self.turno.fecha       = ahora.date()
        self.turno.hora_inicio = ahora.time()
        self.turno.save()
        self.assertFalse(self.reserva.es_cancelable())

    def test_cancelacion_libera_turno(self):
        """CP-16: Al cancelar la reserva el turno vuelve a estar disponible."""
        self.reserva.cancelar()
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_reservado)

    def test_estado_pasa_a_cancelada(self):
        """CP-17: Al cancelar la reserva el estado queda en cancelada."""
        self.reserva.cancelar()
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'cancelada')