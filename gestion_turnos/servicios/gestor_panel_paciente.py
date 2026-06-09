from datetime import date, datetime
from gestion_turnos.models import Reserva

class GestorPanelPaciente:
    """
    Fachada del panel del paciente. Provee los datos necesarios
    para el dashboard e historial del paciente.
    """

    def __init__(self, paciente):
        self.paciente = paciente

    def obtener_proximos_turnos(self, cantidad=3):
        """
        Devuelve los próximos turnos activos del paciente.
        Por defecto devuelve los 3 más próximos para el dashboard.
        """
        ahora = datetime.now().time()
        hoy = date.today()
        return Reserva.objects.filter(
            paciente=self.paciente,
            estado='activa',
            turno__fecha__gte=hoy
        ).exclude(
            turno__fecha=hoy,
            turno__hora_inicio__lt=ahora
        ).select_related('turno__bloque__medico__especialidad'
        ).order_by('turno__fecha', 'turno__hora_inicio')[:cantidad]

    def obtener_historial(self, estado=None, fecha_desde=None, fecha_hasta=None, ascendente=False):
        """
        Devuelve el historial completo de reservas del paciente.
        Permite filtrar por estado y rango de fechas.
        """
        reservas = Reserva.objects.filter(
            paciente=self.paciente
        ).select_related('turno__bloque__medico__especialidad')

        if estado:
            reservas = reservas.filter(estado=estado)
        if fecha_desde:
            reservas = reservas.filter(turno__fecha__gte=fecha_desde)
        if fecha_hasta:
            reservas = reservas.filter(turno__fecha__lte=fecha_hasta)

        if ascendente:
            reservas = reservas.order_by('turno__fecha', 'turno__hora_inicio')
        else:
            reservas = reservas.order_by('-turno__fecha', '-turno__hora_inicio')

        return reservas

    def obtener_detalle_reserva(self, id_reserva):
        """Devuelve el detalle completo de una reserva específica."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            Reserva.objects.filter(paciente=self.paciente).select_related(
                'turno__bloque__medico__especialidad',
                'turno__bloque__medico__clinica'
            ),
            pk=id_reserva
        )