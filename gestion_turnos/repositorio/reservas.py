from datetime import date
from gestion_turnos.models import Turno, Reserva

def obtener_turno_por_id(turno_id):
    """Devuelve un turno con sus relaciones precargadas."""
    return Turno.objects.select_related(
        'bloque__medico__especialidad'
    ).get(pk=turno_id)

def obtener_reservas_paciente(paciente):
    """Devuelve todas las reservas del paciente ordenadas por fecha desc."""
    return Reserva.objects.filter(
        paciente = paciente
    ).select_related(
        'turno__bloque__medico__especialidad'
    ).order_by('-created_at')

def obtener_turnos_disponibles_medico(medico):
    """Devuelve los turnos disponibles futuros de un médico."""
    return Turno.objects.filter(
        bloque__medico = medico,
        fecha__gte     = date.today(),
        esta_reservado = False,            # ← actualizado
        esta_activo    = True              # ← nuevo filtro
    ).order_by('fecha', 'hora_inicio')    # ← actualizado