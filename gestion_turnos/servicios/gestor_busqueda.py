from datetime import date, timedelta
from gestion_turnos.models import Medico, Turno
from django.db.models import Q
from datetime import datetime

class GestorBusqueda:
    """
    Fachada de búsqueda. Centraliza la búsqueda de médicos
    y la consulta de turnos disponibles.
    """
    @staticmethod
    def buscar_medicos(especialidad='', nombre='', ciudad=None, obra_social=None):
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
                Q(clinica__ciudad__nombre__icontains=ciudad) |
                Q(consultorio_particular__ciudad__nombre__icontains=ciudad)
            )

        if obra_social:
            medicos = medicos.filter(
                obras_sociales__nombre__icontains=obra_social
            )

        if nombre:
            medicos = medicos.filter(
                Q(user__first_name__icontains=nombre) |
                Q(user__last_name__icontains=nombre)
            )

        return medicos.distinct()

    @staticmethod
    def obtener_perfil_medico(id_medico):
        """Devuelve el médico con todos sus datos relacionados."""
        from django.shortcuts import get_object_or_404
        return get_object_or_404(
            Medico.objects.filter(estado='aprobado').select_related('especialidad', 'clinica__ciudad'),
            pk=id_medico
        )

    @staticmethod
    def obtener_turnos_disponibles(id_medico, fecha_inicio=None, fecha_fin=None):
        """
        Devuelve los turnos disponibles de un médico agrupados por fecha.
        Si no se pasan fechas, usa hoy + 4 semanas.
        """
        hoy = date.today()
        ahora = datetime.now().time()

        # No permitir fechas pasadas
        if fecha_inicio is None or fecha_inicio < hoy:
            fecha_inicio = hoy
        if fecha_fin is None or fecha_fin < fecha_inicio:
            fecha_fin = fecha_inicio + timedelta(weeks=4)

        turnos = Turno.objects.filter(
            bloque__medico=id_medico,
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin,
            esta_reservado=False,
            esta_activo=True
        ).exclude(
            fecha=hoy,
            hora_inicio__lt=ahora
        ).order_by('fecha', 'hora_inicio')

        # Agrupamos por fecha para mostrar como calendario
        turnos_por_fecha = {}
        for t in turnos:
            turnos_por_fecha.setdefault(t.fecha, []).append(t)

        return turnos_por_fecha

    def obtener_siguiente_semana(fecha_actual):
        """Devuelve la fecha de inicio de la semana siguiente."""
        return fecha_actual + timedelta(weeks=1)

    def obtener_semana_anterior(fecha_actual):
        """Devuelve la fecha de inicio de la semana anterior."""
        return fecha_actual - timedelta(weeks=1)