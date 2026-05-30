from datetime import date
from gestion_turnos.models import Reserva

class GestorPanelPaciente:
    """
    Fachada del panel del paciente. Provee los datos necesarios
    para el dashboard e historial del paciente.
    """

    def obtener_proximos_turnos(self, paciente, cantidad=3):
        """
        Devuelve los próximos turnos activos del paciente.
        Por defecto devuelve los 3 más próximos para el dashboard.
        """
        return Reserva.objects.filter(
            paciente          = paciente,
            estado            = 'activa',
            turno__fecha__gte = date.today()
        ).select_related(
            'turno__bloque__medico__especialidad'
        ).order_by('turno__fecha', 'turno__hora_inicio')[:cantidad]

    def obtener_historial(self, paciente, estado=None, fecha_desde=None, fecha_hasta=None):
        """
        Devuelve el historial completo de reservas del paciente.
        Permite filtrar por estado y rango de fechas.
        """
        reservas = Reserva.objects.filter(
            paciente = paciente
        ).select_related(
            'turno__bloque__medico__especialidad'
        ).order_by('-created_at')

        if estado:
            reservas = reservas.filter(estado=estado)
        if fecha_desde:
            reservas = reservas.filter(turno__fecha__gte=fecha_desde)
        if fecha_hasta:
            reservas = reservas.filter(turno__fecha__lte=fecha_hasta)

        return reservas

    def obtener_detalle_reserva(self, id_reserva):
        """Devuelve el detalle completo de una reserva específica."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            Reserva.objects.select_related(
                'turno__bloque__medico__especialidad',
                'turno__bloque__medico__clinica'
            ),
            pk=id_reserva
        )