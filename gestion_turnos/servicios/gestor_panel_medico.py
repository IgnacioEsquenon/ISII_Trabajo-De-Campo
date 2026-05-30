from datetime import date, timedelta
from gestion_turnos.models import Turno, Reserva

class GestorPanelMedico:
    """
    Fachada del panel del médico. Provee los datos necesarios
    para el dashboard y la agenda semanal.
    """

    def obtener_turnos_del_dia(self, medico, fecha=None):
        """Devuelve los turnos del médico para una fecha específica."""
        fecha = fecha or date.today()
        return Turno.objects.filter(
            bloque__medico = medico,
            fecha          = fecha,
            esta_activo    = True
        ).order_by('hora_inicio')

    def obtener_agenda_semanal(self, medico, fecha_inicio=None):
        """
        Devuelve los turnos de la semana agrupados por fecha.
        Si no se pasa fecha, usa la semana actual.
        """
        fecha_inicio = fecha_inicio or date.today()
        fecha_fin    = fecha_inicio + timedelta(days=6)

        turnos = Turno.objects.filter(
            bloque__medico = medico,
            fecha__gte     = fecha_inicio,
            fecha__lte     = fecha_fin,
            esta_activo    = True
        ).order_by('fecha', 'hora_inicio')

        agenda = {}
        for t in turnos:
            agenda.setdefault(t.fecha, []).append(t)

        return agenda

    def obtener_historial(self, medico, fecha_desde=None, fecha_hasta=None, filtro_paciente=''):
        """
        Devuelve las reservas del médico filtradas por rango de fechas
        y nombre de paciente opcional.
        """
        reservas = Reserva.objects.filter(
            turno__bloque__medico = medico
        ).select_related('turno', 'paciente')

        if fecha_desde:
            reservas = reservas.filter(turno__fecha__gte=fecha_desde)
        if fecha_hasta:
            reservas = reservas.filter(turno__fecha__lte=fecha_hasta)
        if filtro_paciente:
            reservas = reservas.filter(
                paciente__nombre__icontains=filtro_paciente
            )

        return reservas.order_by('turno__fecha', 'turno__hora_inicio')

    def obtener_turnos_semana_anterior(self, medico, fecha_referencia):
        """Devuelve la agenda de la semana anterior a la fecha de referencia."""
        fecha_inicio = fecha_referencia - timedelta(weeks=1)
        return self.obtener_agenda_semanal(medico, fecha_inicio)

    def obtener_turnos_semana_siguiente(self, medico, fecha_referencia):
        """Devuelve la agenda de la semana siguiente a la fecha de referencia."""
        fecha_inicio = fecha_referencia + timedelta(weeks=1)
        return self.obtener_agenda_semanal(medico, fecha_inicio)