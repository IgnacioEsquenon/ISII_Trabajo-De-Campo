from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
from django.db import IntegrityError
from datetime import date, timedelta
from django.views.decorators.cache import never_cache

def get_paciente(request):
    return get_object_or_404(Paciente, user=request.user)

@login_required
def dashboard_paciente(request):
    paciente = get_paciente(request)
    gestor   = GestorPanelPaciente(paciente)
    return render(request, 'paciente/dashboard.html', {
        'paciente': paciente,
        'reservas': gestor.obtener_proximos_turnos(),
    })

@login_required
def buscar_turnos(request):
    from gestion_turnos.models import Ciudad

    # Si viene por GET con parámetros de búsqueda, redirigir a resultados
    if request.method == 'GET' and request.GET:
        especialidad = request.GET.get('especialidad', '').strip()
        ciudad = request.GET.get('ciudad', '').strip()
        obra_social = request.GET.get('obra_social', '').strip()
        nombre = request.GET.get('nombre', '').strip()
        return redirect(
            f"/paciente/resultados/?especialidad={especialidad}"
            f"&ciudad={ciudad}&obra_social={obra_social}&nombre={nombre}"
        )

    # POST tradicional desde el formulario
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        obra_social = request.POST.get('obra_social', '').strip()
        nombre = request.POST.get('nombre', '').strip()

        if not especialidad and not ciudad and not obra_social and not nombre:
            messages.error(request, 'Completá al menos un campo para buscar.')
        else:
            return redirect(
                f"/paciente/resultados/?especialidad={especialidad}"
                f"&ciudad={ciudad}&obra_social={obra_social}&nombre={nombre}"
            )

    return render(request, 'paciente/buscar_turnos.html', {
        'especialidades': Especialidad.objects.all(),
        'ciudades':       Ciudad.objects.all(),
        'obras_sociales': ObraSocial.objects.all(),
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
    medico = GestorBusqueda.obtener_perfil_medico(medico_id)

    # Leer fecha de inicio desde GET (por defecto hoy)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_inicio = date.fromisoformat(fecha_str)
        except ValueError:
            fecha_inicio = date.today()
    else:
        fecha_inicio = date.today()

    fecha_fin = fecha_inicio + timedelta(days=6)

    # Obtener turnos disponibles en el rango
    turnos_por_fecha = GestorBusqueda.obtener_turnos_disponibles(medico_id, fecha_inicio, fecha_fin)

    # Navegación semanal
    semana_anterior = fecha_inicio - timedelta(weeks=1)
    semana_siguiente = fecha_inicio + timedelta(weeks=1)
    dias_semana = [fecha_inicio + timedelta(days=i) for i in range(7)]

    context = {
        'medico': medico,
        'turnos_por_fecha': turnos_por_fecha,
        'dias_semana': dias_semana,
        'fecha_inicio': fecha_inicio,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
        'today': date.today(),
    }
    return render(request, 'paciente/detalle_medico.html', context)

@login_required
def confirmar_turno(request, turno_id):
    paciente = get_paciente(request)
    turno = get_object_or_404(Turno, pk=turno_id)

    if turno.esta_reservado:
        messages.error(request, 'Este turno ya no está disponible.')
        return redirect('detalle_medico', medico_id=turno.bloque.medico.id)

    gestor = GestorReserva()

    if request.method == 'POST':
        try:
            motivo  = request.POST.get('motivo_consulta', '')
            reserva = gestor.reservar_turno(paciente, turno, motivo)
            return redirect('reserva_exitosa', reserva_id=reserva.id)
        except (ValidationError, IntegrityError) as e:
            messages.error(request, 'El turno ya no está disponible.')
            return redirect('detalle_medico', medico_id=turno.bloque.medico.id)

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
    gestor   = GestorPanelPaciente(paciente)

    estado_filtro = request.GET.get('estado', '').strip()

    if estado_filtro == 'activas':
        reservas = gestor.obtener_historial(estado='activa', ascendente=True)
        reservas = reservas.filter(turno__fecha__gte=date.today())
    elif estado_filtro == 'historial':
        # Excluir activas: canceladas y atendidas, más recientes primero
        reservas = gestor.obtener_historial().exclude(estado='activa')
        reservas = reservas.order_by('-turno__fecha', '-turno__hora_inicio')
    else:
        # Mostrar todas, orden ascendente (próximas primero)
        reservas = gestor.obtener_historial(ascendente=True)

    return render(request, 'paciente/mis_turnos.html', {
        'paciente': paciente,
        'reservas': reservas,
        'today':    date.today(),
        'estado_filtro': estado_filtro,
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
    paciente = get_paciente(request)
    obras_sociales = ObraSocial.objects.all()

    if request.method == 'POST':
        obra_social_id = request.POST.get('obra_social')
        obra_social    = None
        if obra_social_id:
            obra_social = ObraSocial.objects.filter(pk=obra_social_id).first()

        paciente.actualizar_datos(
            nombre      = request.POST.get('nombre', paciente.nombre),
            apellido    = request.POST.get('apellido', paciente.apellido),
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

    medicos = GestorBusqueda.buscar_medicos(especialidad, nombre, ciudad)[:5]
    data    = [{'nombre': m.nombre} for m in medicos]
    return JsonResponse(data, safe=False)