from datetime import date, timedelta
from gestion_turnos.models import Turno, Reserva
from django.db.models import Q

class GestorPanelMedico:
    """
    Fachada del panel del médico. Provee los datos necesarios
    para el dashboard y la agenda semanal.
    """
    def __init__(self, medico):
        self.medico = medico
        
    def obtener_turnos_del_dia(self, fecha=None):
        """Devuelve los turnos del médico para una fecha específica."""
        fecha = fecha or date.today()
        return Turno.objects.filter(
            bloque__medico = self.medico,
            fecha          = fecha,
            esta_activo    = True
        ).order_by('hora_inicio')

    def obtener_agenda_semanal(self, fecha_inicio=None):
        fecha_inicio = fecha_inicio or date.today()
        fecha_fin = fecha_inicio + timedelta(days=6)

        reservas = Reserva.objects.filter(
            turno__bloque__medico=self.medico,
            estado='activa',
            turno__fecha__gte=fecha_inicio,
            turno__fecha__lte=fecha_fin
        ).select_related('turno', 'paciente').order_by('turno__fecha', 'turno__hora_inicio')

        agenda = {}
        for r in reservas:
            agenda.setdefault(r.turno.fecha, []).append(r)
        return agenda

    def obtener_historial(self, fecha_desde=None, fecha_hasta=None, filtro_paciente='', estado=None):
        """
        Devuelve las reservas del médico filtradas por rango de fechas
        y nombre de paciente opcional.
        """
        reservas = Reserva.objects.filter(
            turno__bloque__medico=self.medico
        ).select_related('turno', 'paciente')

        if fecha_desde:
            reservas = reservas.filter(turno__fecha__gte=fecha_desde)
        if fecha_hasta:
            reservas = reservas.filter(turno__fecha__lte=fecha_hasta)
        if filtro_paciente:
            reservas = reservas.filter(
                Q(paciente__nombre__icontains=filtro_paciente) |
                Q(paciente__apellido__icontains=filtro_paciente) |
                Q(paciente__dni__icontains=filtro_paciente)
            )
        if estado is not None:
            reservas = reservas.filter(estado__in=estado)

        return reservas.order_by('-turno__fecha', '-turno__hora_inicio')

    def obtener_turnos_semana_anterior(self, fecha_referencia):
        """Devuelve la agenda de la semana anterior a la fecha de referencia."""
        fecha_inicio = fecha_referencia - timedelta(weeks=1)
        return self.obtener_agenda_semanal(fecha_inicio)

    def obtener_turnos_semana_siguiente(self, fecha_referencia):
        """Devuelve la agenda de la semana siguiente a la fecha de referencia."""
        fecha_inicio = fecha_referencia + timedelta(weeks=1)
        return self.obtener_agenda_semanal(fecha_inicio)