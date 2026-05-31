from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from gestion_turnos.models import Paciente, Especialidad, ObraSocial, Turno, Reserva
from gestion_turnos.servicios.gestor_busqueda import GestorBusqueda
from gestion_turnos.servicios.gestor_reserva import GestorReserva
from gestion_turnos.servicios.gestor_panel_paciente import GestorPanelPaciente

def get_paciente(request):
    return get_object_or_404(Paciente, user=request.user)

@login_required
def dashboard_paciente(request):
    paciente = get_paciente(request)
    gestor   = GestorPanelPaciente()
    return render(request, 'paciente/dashboard.html', {
        'paciente': paciente,
        'reservas': gestor.obtener_proximos_turnos(paciente),
    })

@login_required
def buscar_turnos(request):
    from gestion_turnos.models import Ciudad
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad', '').strip()
        ciudad       = request.POST.get('ciudad', '').strip()
        obra_social  = request.POST.get('obra_social', '').strip()

        # Al menos un campo debe estar completo
        if not especialidad and not ciudad and not obra_social:
            messages.error(request, 'Completá al menos un campo para buscar.')
        else:
            return redirect(
                f"/paciente/resultados/?especialidad={especialidad}"
                f"&ciudad={ciudad}&obra_social={obra_social}"
            )

    return render(request, 'paciente/buscar_turnos.html', {
        'especialidades': Especialidad.objects.all(),
        'ciudades':       Ciudad.objects.all(),
        'obras_sociales': ObraSocial.objects.all(),  # ← nuevo
    })

@login_required
def resultados_busqueda(request):
    from django.core.paginator import Paginator
    especialidad = request.GET.get('especialidad', '')
    ciudad       = request.GET.get('ciudad', '')
    obra_social  = request.GET.get('obra_social', '')

    gestor  = GestorBusqueda()
    medicos = gestor.buscar_medicos(especialidad, ciudad=ciudad, obra_social=obra_social)

    paginator = Paginator(medicos, 5)
    pagina    = paginator.get_page(request.GET.get('page'))

    return render(request, 'paciente/resultados_busqueda.html', {
        'medicos':      pagina,
        'especialidad': especialidad,
        'ciudad':       ciudad,
        'obra_social':  obra_social,
    })

@login_required
def detalle_medico(request, medico_id):
    gestor = GestorBusqueda()
    medico = gestor.obtener_perfil_medico(medico_id)

    return render(request, 'paciente/detalle_medico.html', {
        'medico':           medico,
        'turnos_por_fecha': gestor.obtener_turnos_disponibles(medico_id),
    })

@login_required
def confirmar_turno(request, turno_id):
    paciente = get_paciente(request)
    turno    = get_object_or_404(Turno, pk=turno_id, esta_reservado=False)
    gestor   = GestorReserva()

    if request.method == 'POST':
        try:
            motivo  = request.POST.get('motivo_consulta', '')
            reserva = gestor.reservar_turno(paciente, turno, motivo)
            return redirect('reserva_exitosa', reserva_id=reserva.id)
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, 'paciente/confirmar_turno.html', {
        'turno':    turno,
        'paciente': paciente,
    })

@login_required
def reserva_exitosa(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, paciente__user=request.user)
    return render(request, 'paciente/reserva_exitosa.html', {'reserva': reserva})

@login_required
def mis_turnos(request):
    paciente = get_paciente(request)
    gestor   = GestorPanelPaciente()
    return render(request, 'paciente/mis_turnos.html', {
    'paciente': paciente,
    'reservas': gestor.obtener_historial(paciente),
    'today':    date.today(),   
    })

@login_required
def cancelar_turno(request, reserva_id):
    paciente = get_paciente(request)
    reserva  = get_object_or_404(Reserva, pk=reserva_id, paciente=paciente, estado='activa')
    gestor   = GestorReserva()

    if request.method == 'POST':
        try:
            gestor.cancelar_reserva(reserva)
            messages.success(request, 'Turno cancelado correctamente.')
            return redirect('mis_turnos')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('mis_turnos')

    return render(request, 'paciente/cancelar_turno.html', {'reserva': reserva})

@login_required
def perfil_paciente(request):
    paciente     = get_paciente(request)
    obras_sociales = ObraSocial.objects.all()  # ← lo sacás arriba, fuera del if

    if request.method == 'POST':
        obra_social_id = request.POST.get('obra_social')
        obra_social    = None
        if obra_social_id:
            obra_social = ObraSocial.objects.filter(pk=obra_social_id).first()

        paciente.actualizar_datos(
            telefono    = request.POST.get('telefono', paciente.telefono),
            obra_social = obra_social
        )
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('perfil_paciente')

    return render(request, 'paciente/perfil_paciente.html', {
        'paciente':       paciente,
        'obras_sociales': obras_sociales,
    })

@login_required
def autocomplete_medico(request):
    especialidad = request.GET.get('especialidad', '')
    nombre       = request.GET.get('nombre', '')
    ciudad       = request.GET.get('ciudad', '')

    gestor  = GestorBusqueda()
    medicos = gestor.buscar_medicos(especialidad, nombre, ciudad)[:5]
    data    = [{'nombre': m.nombre} for m in medicos]
    return JsonResponse(data, safe=False)