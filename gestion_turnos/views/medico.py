from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from gestion_turnos.models import Medico, BloqueHorario, Turno, Reserva
from gestion_turnos.forms import BloqueHorarioForm
from gestion_turnos.servicios.gestor_agenda import GestorAgenda
from gestion_turnos.servicios.gestor_panel_medico import GestorPanelMedico
from gestion_turnos.servicios.gestor_reserva import GestorReserva
from django.views.decorators.http import require_POST

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

    return redirect('configurar_bloques', medico_id=medico_id)

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
                return redirect('configurar_bloques', medico_id=bloque.medico.id)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = BloqueHorarioForm(instance=bloque)

    return render(request, 'editar_bloque.html', {
        'form':   form,
        'bloque': bloque,
    })

    
@login_required
def confirmar_atencion(request, reserva_id):
    medico = get_object_or_404(Medico, user=request.user)
    reserva = get_object_or_404(Reserva, pk=reserva_id, turno__bloque__medico=medico)

    if reserva.estado != 'activa':
        messages.warning(request, 'Esta reserva ya fue atendida o cancelada.')
        return redirect('agenda_semanal', medico_id=medico.id)

    gestor = GestorReserva()

    if request.method == 'POST':
        diagnostico = request.POST.get('diagnostico', '')
        try:
            gestor.confirmar_atencion(reserva, diagnostico)
            messages.success(request, 'Atención confirmada correctamente.')
            return redirect('agenda_semanal', medico_id=medico.id)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('agenda_semanal', medico_id=medico.id)

    return render(request, 'confirmar_atencion.html', {'reserva': reserva})

@login_required
def agenda_semanal(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)
    gestor = GestorPanelMedico(medico)

    # Leer fecha de inicio desde GET, por defecto hoy
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_inicio = date.fromisoformat(fecha_str)
        except ValueError:
            fecha_inicio = date.today()
    else:
        fecha_inicio = date.today()

    # Obtener agenda semanal
    agenda = gestor.obtener_agenda_semanal(fecha_inicio)

    # Calcular semana siguiente y anterior
    semana_anterior = fecha_inicio - timedelta(weeks=1)
    semana_siguiente = fecha_inicio + timedelta(weeks=1)

    # Generar lista de 7 días para la grilla
    dias_semana = [fecha_inicio + timedelta(days=i) for i in range(7)]

    context = {
        'medico': medico,
        'agenda': agenda,               # Dict[Date, List[Reserva]]
        'dias_semana': dias_semana,
        'fecha_inicio': fecha_inicio,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
    }
    return render(request, 'agenda_semanal.html', context)

@login_required
def configurar_bloques(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)
    gestor = GestorAgenda(medico)

    form = BloqueHorarioForm()

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
                return redirect('configurar_bloques', medico_id=medico.id)
            except ValidationError as e:
                form.add_error(None, e)

    bloques_por_dia = gestor.obtener_estructura_bloques()

    # ── Construir turnos agrupados por fecha para cada bloque ──
    turnos_por_bloque = {}
    for dia, bloques in bloques_por_dia.items():
        for bloque in bloques:
            # obtener_turnos() devuelve todos los turnos futuros activos (libres y reservados)
            turnos = bloque.obtener_turnos()
            por_fecha = {}
            for t in turnos:
                por_fecha.setdefault(t.fecha, []).append(t)
            turnos_por_bloque[bloque.id] = por_fecha

    context = {
        'medico': medico,
        'form': form,
        'bloques_por_dia': bloques_por_dia,
        'turnos_por_bloque': turnos_por_bloque,
    }
    return render(request, 'configurar_bloques.html', context)

@login_required
def historial_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)
    gestor = GestorPanelMedico(medico)

    # Filtros desde GET
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    filtro_paciente = request.GET.get('paciente', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    if fecha_desde:
        fecha_desde = date.fromisoformat(fecha_desde) if fecha_desde else None
    if fecha_hasta:
        fecha_hasta = date.fromisoformat(fecha_hasta) if fecha_hasta else None

    # Mapeo de estados según el filtro seleccionado
    if estado_filtro == 'canceladas':
        estados = ['cancelada']
    elif estado_filtro == 'atendidas':
        estados = ['atendida']
    else:
        estados = ['atendida', 'cancelada']   # "Todas"

    reservas = gestor.obtener_historial(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        filtro_paciente=filtro_paciente,
        estado=estados,
    )

    context = {
        'medico': medico,
        'reservas': reservas,
        'fecha_desde': request.GET.get('fecha_desde', ''),
        'fecha_hasta': request.GET.get('fecha_hasta', ''),
        'filtro_paciente': filtro_paciente,
        'estado_filtro': estado_filtro,
    }
    return render(request, 'historial_medico.html', context)