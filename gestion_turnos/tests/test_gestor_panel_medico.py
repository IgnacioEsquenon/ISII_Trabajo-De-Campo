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
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        self.hoy      = date.today()
        # Crear turno y reserva activa para hoy
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
            turno=self.turno, paciente=self.paciente, estado='activa'
        )
        # Instanciar el gestor con el médico
        self.gestor   = GestorPanelMedico(self.medico)

    # ------------------------------------------------------------
    # obtener_turnos_del_dia (devuelve turnos, no reservas)
    # ------------------------------------------------------------
    def test_obtener_turnos_del_dia_devuelve_turnos_de_hoy(self):
        resultado = self.gestor.obtener_turnos_del_dia(self.hoy)
        self.assertIn(self.turno, resultado)

    def test_obtener_turnos_del_dia_no_devuelve_otros_dias(self):
        resultado = self.gestor.obtener_turnos_del_dia(self.hoy + timedelta(days=1))
        self.assertNotIn(self.turno, resultado)

    # ------------------------------------------------------------
    # obtener_agenda_semanal (devuelve reservas activas agrupadas por fecha)
    # ------------------------------------------------------------
    def test_obtener_agenda_semanal_agrupa_por_fecha(self):
        resultado = self.gestor.obtener_agenda_semanal(self.hoy)
        self.assertIsInstance(resultado, dict)
        # Debe contener la reserva de hoy
        self.assertIn(self.hoy, resultado)
        self.assertIn(self.reserva, resultado[self.hoy])

    def test_obtener_agenda_semanal_no_incluye_reservas_canceladas(self):
        self.reserva.estado = 'cancelada'
        self.reserva.save()
        resultado = self.gestor.obtener_agenda_semanal(self.hoy)
        # No debe aparecer porque solo se incluyen activas
        self.assertNotIn(self.hoy, resultado)

    # ------------------------------------------------------------
    # obtener_historial
    # ------------------------------------------------------------
    def test_obtener_historial_devuelve_reservas(self):
        resultado = self.gestor.obtener_historial()
        self.assertIn(self.reserva, resultado)

    def test_obtener_historial_filtra_por_fecha(self):
        resultado = self.gestor.obtener_historial(fecha_desde=self.hoy + timedelta(days=1))
        self.assertNotIn(self.reserva, resultado)

    # ------------------------------------------------------------
    # obtener_turnos_semana_siguiente / anterior (devuelven reservas)
    # ------------------------------------------------------------
    def test_obtener_turnos_semana_siguiente(self):
        # Crear turno y reserva activa para la próxima semana
        fecha_futura = self.hoy + timedelta(weeks=1)
        turno_futuro = Turno.objects.create(
            bloque=self.bloque, fecha=fecha_futura,
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        reserva_futura = Reserva.objects.create(
            turno=turno_futuro, paciente=self.paciente, estado='activa'
        )
        resultado = self.gestor.obtener_turnos_semana_siguiente(self.hoy)
        self.assertIn(fecha_futura, resultado)
        self.assertIn(reserva_futura, resultado[fecha_futura])

    def test_obtener_turnos_semana_anterior(self):
        fecha_pasada = self.hoy - timedelta(weeks=1)
        turno_pasado = Turno.objects.create(
            bloque=self.bloque, fecha=fecha_pasada,
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        reserva_pasada = Reserva.objects.create(
            turno=turno_pasado, paciente=self.paciente, estado='activa'
        )
        resultado = self.gestor.obtener_turnos_semana_anterior(self.hoy)
        self.assertIn(fecha_pasada, resultado)
        self.assertIn(reserva_pasada, resultado[fecha_pasada])