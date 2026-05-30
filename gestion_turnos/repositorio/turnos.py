from datetime import date
from gestion_turnos.models import Turno, BloqueHorario

def obtener_turnos_por_fecha(medico, desde=None):
    """Devuelve turnos activos del médico agrupados por fecha."""
    desde     = desde or date.today()
    turnos_db = Turno.objects.filter(
        bloque__medico = medico,
        fecha__gte     = desde,
        esta_activo    = True          # ← actualizado
    ).order_by('fecha', 'hora_inicio') # ← actualizado

    turnos_por_fecha = {}
    for t in turnos_db:
        turnos_por_fecha.setdefault(t.fecha, []).append(t)
    return turnos_por_fecha

def obtener_bloques_por_dia(medico):
    """Devuelve bloques activos del médico agrupados por día."""
    bloques_por_dia = {}
    for b in medico.bloques.filter(activo=True):  # ← filtra solo activos
        dia = b.get_dia_semana_display()
        bloques_por_dia.setdefault(dia, []).append(b)
    return bloques_por_dia

def guardar_turnos(bloque, turnos_data):
    """
    Persiste los turnos en la DB.
    Filtra franjas ya reservadas para no generar duplicados.
    """
    reservados = {
        (t.fecha, t.hora_inicio)          # ← actualizado
        for t in Turno.objects.filter(
            bloque__medico = bloque.medico,
            esta_reservado = True,         # ← actualizado
            fecha__gte     = date.today()
        )
    }

    objetos = [
        Turno(bloque=bloque, **t)
        for t in turnos_data
        if (t['fecha'], t['hora_inicio']) not in reservados  # ← actualizado
    ]

    if objetos:
        Turno.objects.bulk_create(objetos)

def borrar_turnos_futuros(bloque):
    """Borra solo los turnos futuros no reservados del bloque."""
    Turno.objects.filter(
        bloque         = bloque,
        fecha__gte     = date.today(),
        esta_reservado = False             # ← actualizado
    ).delete()