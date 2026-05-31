from datetime import date, timedelta
from gestion_turnos.models import Medico, Turno

class GestorBusqueda:
    """
    Fachada de búsqueda. Centraliza la búsqueda de médicos
    y la consulta de turnos disponibles.
    """

    def buscar_medicos(self, especialidad='', nombre='', ciudad=None, obra_social=None):
        """
        Busca médicos aprobados filtrando por cualquier combinación
        de especialidad, ciudad y obra social.
        Al menos uno debe tener valor.
        """
        medicos = Medico.objects.filter(estado='aprobado')

        if especialidad:
            medicos = medicos.filter(
                especialidad__nombre__icontains=especialidad
            )

        if ciudad:
            medicos = medicos.filter(
                clinica__ciudad__nombre__icontains=ciudad
            )

        if obra_social:
            medicos = medicos.filter(
                obras_sociales__nombre__icontains=obra_social
            )

        if nombre:
            medicos = medicos.filter(nombre__icontains=nombre)

        return medicos.distinct()

    def obtener_perfil_medico(self, id_medico):
        """Devuelve el médico con todos sus datos relacionados."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            Medico.objects.select_related('especialidad', 'clinica__ciudad'),
            pk=id_medico
        )

    def obtener_turnos_disponibles(self, id_medico, fecha_inicio=None, fecha_fin=None, limite_horas=None):
        """
        Devuelve los turnos disponibles de un médico agrupados por fecha.
        Si no se pasan fechas, usa hoy + 4 semanas.
        """
        fecha_inicio = fecha_inicio or date.today()
        fecha_fin    = fecha_fin    or (fecha_inicio + timedelta(weeks=4))

        turnos = Turno.objects.filter(
            bloque__medico = id_medico,
            fecha__gte     = fecha_inicio,
            fecha__lte     = fecha_fin,
            esta_reservado = False,
            esta_activo    = True
        ).order_by('fecha', 'hora_inicio')

        # Agrupamos por fecha para mostrar como calendario
        turnos_por_fecha = {}
        for t in turnos:
            turnos_por_fecha.setdefault(t.fecha, []).append(t)

        return turnos_por_fecha

    def obtener_siguiente_semana(self, fecha_actual):
        """Devuelve la fecha de inicio de la semana siguiente."""
        return fecha_actual + timedelta(weeks=1)

    def obtener_semana_anterior(self, fecha_actual):
        """Devuelve la fecha de inicio de la semana anterior."""
        return fecha_actual - timedelta(weeks=1)