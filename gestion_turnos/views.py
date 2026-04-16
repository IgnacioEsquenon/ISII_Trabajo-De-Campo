from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Medico, BloqueHorario
from .forms import BloqueHorarioForm

# Creamos las vistas 
@login_required
def agenda_medico(request, medico_id):
    medico  = get_object_or_404(Medico, pk=medico_id, user=request.user)
    bloques = medico.bloques.all()

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST)
        if form.is_valid():
            bloque        = form.save(commit=False)
            bloque.medico = medico
            bloque.save()
            messages.success(request, 'Bloque creado correctamente.')
            return redirect('agenda_medico', medico_id=medico.id)
    else:
        form = BloqueHorarioForm()

    bloques_por_dia = {}
    for b in bloques:
        dia = b.get_dia_semana_display()
        bloques_por_dia.setdefault(dia, []).append(b)

    return render(request, 'agenda_medico.html', {
        'medico':         medico,
        'form':           form,
        'bloques_por_dia': bloques_por_dia,
    })

def toggle_bloque(request, bloque_id):
    bloque        = get_object_or_404(BloqueHorario, pk=bloque_id)
    bloque.activo = not bloque.activo
    bloque.save()
    return redirect('agenda_medico', medico_id=bloque.medico.id)

def eliminar_bloque(request, bloque_id):
    bloque    = get_object_or_404(BloqueHorario, pk=bloque_id)
    medico_id = bloque.medico.id
    bloque.delete()
    messages.success(request, 'Bloque eliminado.')
    return redirect('agenda_medico', medico_id=medico_id)

