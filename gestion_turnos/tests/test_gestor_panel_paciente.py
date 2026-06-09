from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, Especialidad, BloqueHorario, Turno, Reserva
)
from gestion_turnos.servicios.gestor_panel_paciente import GestorPanelPaciente


class TestGestorPanelPaciente(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user_med      = User.objects.create_user(username='medico8', password='1234')
        medico        = Medico.objects.create(
            user=user_med, nombre='García', matricula='M008',
            especialidad=especialidad, estado='aprobado'
        )
        bloque        = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        self.turno    = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        user_pac      = User.objects.create_user(username='paciente4', password='1234')
        self.paciente = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='33333333'
        )
        self.reserva  = Reserva.objects.create(
            turno=self.turno, paciente=self.paciente, estado='activa'
        )
        # Instanciar el gestor con el paciente
        self.gestor   = GestorPanelPaciente(self.paciente)

    def test_obtener_proximos_turnos(self):
        """obtener_proximos_turnos devuelve reservas activas futuras."""
        resultado = self.gestor.obtener_proximos_turnos()
        self.assertIn(self.reserva, resultado)

    def test_obtener_proximos_turnos_respeta_cantidad(self):
        """obtener_proximos_turnos respeta el límite de cantidad."""
        resultado = self.gestor.obtener_proximos_turnos(cantidad=1)
        self.assertEqual(len(resultado), 1)

    def test_obtener_proximos_turnos_no_incluye_canceladas(self):
        """obtener_proximos_turnos no incluye reservas canceladas."""
        self.reserva.estado = 'cancelada'
        self.reserva.save()
        resultado = self.gestor.obtener_proximos_turnos()
        self.assertNotIn(self.reserva, resultado)

    def test_obtener_historial_devuelve_todas(self):
        """obtener_historial devuelve todas las reservas del paciente."""
        resultado = self.gestor.obtener_historial()
        self.assertIn(self.reserva, resultado)

    def test_obtener_historial_filtra_por_estado(self):
        """obtener_historial filtra correctamente por estado."""
        resultado = self.gestor.obtener_historial(estado='cancelada')
        self.assertNotIn(self.reserva, resultado)

    def test_obtener_historial_filtra_por_fecha(self):
        """obtener_historial filtra por rango de fechas."""
        resultado = self.gestor.obtener_historial(
            fecha_desde=date.today() + timedelta(days=30)
        )
        self.assertNotIn(self.reserva, resultado)

    def test_obtener_detalle_reserva(self):
        """obtener_detalle_reserva devuelve la reserva correcta."""
        resultado = self.gestor.obtener_detalle_reserva(self.reserva.pk)
        self.assertEqual(resultado.pk, self.reserva.pk)