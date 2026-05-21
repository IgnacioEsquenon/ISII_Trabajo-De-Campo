from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from gestion_turnos.models import Medico, BloqueHorario
from gestion_turnos.forms import BloqueHorarioForm
from gestion_turnos.servicios.turnos import crear_bloque_con_turnos
from gestion_turnos.repositorio.turnos import obtener_turnos_por_fecha, obtener_bloques_por_dia
from gestion_turnos.servicios.turnos import crear_bloque_con_turnos, editar_bloque_con_turnos

@login_required
def agenda_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST)
        if form.is_valid():
            ok, error = crear_bloque_con_turnos(medico, form)
            if ok:
                messages.success(request, 'Bloque y turnos creados correctamente.')
                return redirect('agenda_medico', medico_id=medico.id)
            form.add_error(None, error)
    else:
        form = BloqueHorarioForm()

    return render(request, 'agenda_medico.html', {
        'medico':           medico,
        'form':             form,
        'bloques_por_dia':  obtener_bloques_por_dia(medico),
        'turnos_por_fecha': obtener_turnos_por_fecha(medico, date.today()),
    })

def eliminar_bloque(request, bloque_id):
    bloque    = get_object_or_404(BloqueHorario, pk=bloque_id)
    medico_id = bloque.medico.id
    bloque.delete()
    messages.success(request, 'Bloque eliminado.')
    return redirect('agenda_medico', medico_id=medico_id)

@login_required
def editar_bloque(request, bloque_id):
    bloque = get_object_or_404(BloqueHorario, pk=bloque_id, medico__user=request.user)

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST, instance=bloque)
        if form.is_valid():
            ok, error = editar_bloque_con_turnos(bloque, form)
            if ok:
                messages.success(request, 'Bloque actualizado y turnos regenerados.')
                return redirect('agenda_medico', medico_id=bloque.medico.id)
            form.add_error(None, error)
    else:
        form = BloqueHorarioForm(instance=bloque)  # precarga los datos actuales

    return render(request, 'editar_bloque.html', {
        'form':   form,
        'bloque': bloque,
    })