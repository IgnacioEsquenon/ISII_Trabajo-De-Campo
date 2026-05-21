# services/turnos.py
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from gestion_turnos.models import BloqueHorario
from gestion_turnos.repositorio.turnos import guardar_turnos

def crear_bloque_con_turnos(medico, form):
    bloque = form.save(commit=False)
    bloque.medico = medico

    try:
        bloque.full_clean()
        validar_superposicion(bloque)
        bloque.save()
        turnos = calcular_turnos(bloque)
        guardar_turnos(bloque, turnos)
        return True, None
    except ValidationError as e:
        return False, e

def validar_superposicion(bloque):
    bloques_existentes = BloqueHorario.objects.filter(
        medico_id  = bloque.medico_id,
        dia_semana = bloque.dia_semana
    )
    if bloque.pk:
        bloques_existentes = bloques_existentes.exclude(pk=bloque.pk)

    for b in bloques_existentes:
        if bloque.hora_inicio < b.hora_fin and bloque.hora_fin > b.hora_inicio:
            raise ValidationError(
                f"Se superpone con bloque existente: {b.hora_inicio.strftime('%H:%M')} a {b.hora_fin.strftime('%H:%M')}."
            )

def calcular_turnos(bloque, semanas=4):
    hoy                = date.today()
    dias_para_proximo  = (bloque.dia_semana - hoy.weekday()) % 7
    proxima_fecha      = hoy + timedelta(days=dias_para_proximo)
    fechas             = [proxima_fecha + timedelta(weeks=i) for i in range(semanas)]

    inicio_dt = datetime.combine(hoy, bloque.hora_inicio)
    fin_dt    = datetime.combine(hoy, bloque.hora_fin)
    turnos    = []

    for fecha in fechas:
        actual = inicio_dt
        while (actual + timedelta(minutes=bloque.duracion_turno)) <= fin_dt:
            turnos.append({
                'fecha':  fecha,
                'hora':   actual.time(),
                'estado': 'disponible'
            })
            actual += timedelta(minutes=bloque.duracion_turno)

    return turnos

def editar_bloque_con_turnos(bloque, form):
    form_data = form.save(commit=False)
    bloque.dia_semana     = form_data.dia_semana
    bloque.hora_inicio    = form_data.hora_inicio
    bloque.hora_fin       = form_data.hora_fin
    bloque.duracion_turno = form_data.duracion_turno

    try:
        bloque.full_clean()
        validar_superposicion(bloque)
        bloque.save()

        # Borramos los turnos actuales y recargamos con los nuevos horarios
        from gestion_turnos.repositorio.turnos import borrar_turnos_futuros, guardar_turnos
        borrar_turnos_futuros(bloque)
        turnos = calcular_turnos(bloque)
        guardar_turnos(bloque, turnos)
        return True, None
    except ValidationError as e:
        return False, e