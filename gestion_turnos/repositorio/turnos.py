from gestion_turnos.models import Turno

def obtener_turnos_por_fecha(medico, desde):
    turnos_db = Turno.objects.filter(
        bloque__medico=medico,
        fecha__gte=desde
    ).order_by('fecha', 'hora')

    turnos_por_fecha = {}
    for t in turnos_db:
        turnos_por_fecha.setdefault(t.fecha, []).append(t)

    return turnos_por_fecha

def obtener_bloques_por_dia(medico):
    bloques_por_dia = {}
    for b in medico.bloques.all():
        dia = b.get_dia_semana_display()
        bloques_por_dia.setdefault(dia, []).append(b)

    return bloques_por_dia

def guardar_turnos(bloque, turnos_data):
    objetos = [Turno(bloque=bloque, **t) for t in turnos_data]
    Turno.objects.bulk_create(objetos)