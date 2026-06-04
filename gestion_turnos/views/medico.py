from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from gestion_turnos.models import Medico, BloqueHorario
from gestion_turnos.forms import BloqueHorarioForm
from gestion_turnos.servicios.gestor_agenda import GestorAgenda
from gestion_turnos.repositorio.turnos import obtener_turnos_por_fecha

@login_required
def agenda_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)
    gestor = GestorAgenda(medico)

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST)
        if form.is_valid():
            try:
                gestor.crear_bloque_horario(
                    dia_semana     = form.cleaned_data['dia_semana'],
                    hora_inicio    = form.cleaned_data['hora_inicio'],
                    hora_fin       = form.cleaned_data['hora_fin'],
                    duracion_turno = form.cleaned_data['duracion_turno'],
                )
                messages.success(request, 'Bloque y turnos creados correctamente.')
                return redirect('agenda_medico', medico_id=medico.id)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = BloqueHorarioForm()

    # Turnos reservados futuros con datos del paciente
    from gestion_turnos.models import Turno
    from datetime import date
    turnos_reservados = Turno.objects.filter(
        bloque__medico = medico,
        esta_reservado = True,
        fecha__gte     = date.today()
    ).select_related(
        'reserva__paciente'
    ).order_by('fecha', 'hora_inicio')

    return render(request, 'agenda_medico.html', {
        'medico':            medico,
        'form':              form,
        'bloques_por_dia':   gestor.obtener_estructura_bloques(),
        'turnos_por_fecha':  obtener_turnos_por_fecha(medico),
        'turnos_reservados': turnos_reservados,   # ← nuevo
    })

@login_required
@require_POST  # ← solo acepta POST, evita eliminación por GET
def eliminar_bloque(request, bloque_id):
    # Ownership check — solo el dueño del bloque puede eliminarlo
    bloque    = get_object_or_404(BloqueHorario, pk=bloque_id, medico__user=request.user)
    medico_id = bloque.medico.id
    gestor    = GestorAgenda(bloque.medico)

    try:
        gestor.eliminar_bloque_horario(bloque)
        messages.success(request, 'Bloque eliminado correctamente.')
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect('agenda_medico', medico_id=medico_id)

@login_required
def editar_bloque(request, bloque_id):
    bloque = get_object_or_404(BloqueHorario, pk=bloque_id, medico__user=request.user)
    gestor = GestorAgenda(bloque.medico)

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST, instance=bloque)
        if form.is_valid():
            try:
                gestor.editar_bloque_horario(
                    bloque         = bloque,
                    dia_semana     = form.cleaned_data['dia_semana'],
                    hora_inicio    = form.cleaned_data['hora_inicio'],
                    hora_fin       = form.cleaned_data['hora_fin'],
                    duracion_turno = form.cleaned_data['duracion_turno'],
                )
                messages.success(request, 'Bloque actualizado correctamente.')
                return redirect('agenda_medico', medico_id=bloque.medico.id)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = BloqueHorarioForm(instance=bloque)

    return render(request, 'editar_bloque.html', {
        'form':   form,
        'bloque': bloque,
    })