from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, Especialidad, BloqueHorario, Turno, Reserva
)
from gestion_turnos.servicios.gestor_panel_medico import GestorPanelMedico


class TestGestorPanelMedico(TestCase):

    def setUp(self):
        especialidad  = Especialidad.objects.create(nombre='Cardiología')
        user_med      = User.objects.create_user(username='medico7', password='1234')
        self.medico   = Medico.objects.create(
            user=user_med, nombre='García', matricula='M007',
            especialidad=especialidad, estado='aprobado'
        )
        self.bloque   = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        self.hoy      = date.today()
        self.turno    = Turno.objects.create(
            bloque=self.bloque, fecha=self.hoy,
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        user_pac      = User.objects.create_user(username='paciente3', password='1234')
        self.paciente = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='22222222'
        )
        self.reserva  = Reserva.objects.create(
            turno=self.turno, paciente=self.paciente
        )
        self.gestor   = GestorPanelMedico()

    def test_obtener_turnos_del_dia(self):
        """obtener_turnos_del_dia devuelve turnos de la fecha indicada."""
        resultado = self.gestor.obtener_turnos_del_dia(self.medico, self.hoy)
        self.assertIn(self.turno, resultado)

    def test_obtener_turnos_del_dia_no_devuelve_otros_dias(self):
        """obtener_turnos_del_dia no devuelve turnos de otros días."""
        resultado = self.gestor.obtener_turnos_del_dia(
            self.medico, self.hoy + timedelta(days=1)
        )
        self.assertNotIn(self.turno, resultado)

    def test_obtener_agenda_semanal_agrupa_por_fecha(self):
        """obtener_agenda_semanal devuelve dict agrupado por fecha."""
        resultado = self.gestor.obtener_agenda_semanal(self.medico, self.hoy)
        self.assertIsInstance(resultado, dict)

    def test_obtener_historial_devuelve_reservas(self):
        """obtener_historial devuelve las reservas del médico."""
        resultado = self.gestor.obtener_historial(self.medico)
        self.assertIn(self.reserva, resultado)

    def test_obtener_historial_filtra_por_fecha(self):
        """obtener_historial filtra correctamente por fecha desde."""
        resultado = self.gestor.obtener_historial(
            self.medico,
            fecha_desde=self.hoy + timedelta(days=1)
        )
        self.assertNotIn(self.reserva, resultado)

    def test_obtener_turnos_semana_siguiente(self):
        """obtener_turnos_semana_siguiente devuelve la semana correcta."""
        turno_futuro = Turno.objects.create(
            bloque=self.bloque,
            fecha=self.hoy + timedelta(weeks=1),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        resultado = self.gestor.obtener_turnos_semana_siguiente(
            self.medico, self.hoy
        )
        fechas = list(resultado.keys())
        self.assertIn(turno_futuro.fecha, fechas)

    def test_obtener_turnos_semana_anterior(self):
        """obtener_turnos_semana_anterior devuelve la semana correcta."""
        turno_pasado = Turno.objects.create(
            bloque=self.bloque,
            fecha=self.hoy - timedelta(weeks=1),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        resultado = self.gestor.obtener_turnos_semana_anterior(
            self.medico, self.hoy
        )
        fechas = list(resultado.keys())
        self.assertIn(turno_pasado.fecha, fechas)
