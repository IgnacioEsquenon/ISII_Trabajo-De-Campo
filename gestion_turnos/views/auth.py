from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from gestion_turnos.forms import RegistroMedicoForm, RegistroPacienteForm
from gestion_turnos.servicios.usuarios import resolver_destino_usuario
from gestion_turnos.servicios.registro import Registro
from datetime import date, timedelta

def home_principal(request):
    if request.user.is_authenticated:
        ruta, kwargs = resolver_destino_usuario(request.user)
        return redirect(ruta, **kwargs)
    
    from gestion_turnos.models import Especialidad, ObraSocial
    
    return render(request, 'home_principal.html', {
        'especialidades': Especialidad.objects.all(),
        'obras_sociales': ObraSocial.objects.all(),
    })

def seleccionar_registro(request):
    if request.user.is_authenticated:
        return redirect('home_principal')
    return render(request, 'seleccionar_registro.html')

def registro_medico(request):
    if request.user.is_authenticated:
        return redirect('home_principal')

    if request.method == 'POST':
        form = RegistroMedicoForm(request.POST)
        if form.is_valid():
            try:
                # Validamos unicidad antes de crear
                Registro.validar_unicidad(
                    email     = form.cleaned_data['email'] if 'email' in form.cleaned_data else None,
                    matricula = form.cleaned_data['matricula']
                )
                usuario = Registro.registrar_usuario(form)
                Registro.registrar_medico(
                usuario        = usuario,
                matricula      = form.cleaned_data['matricula'],
                especialidad   = form.cleaned_data['especialidad'],
                clinica        = form.cleaned_data.get('clinica'),
                obras_sociales = form.cleaned_data.get('obras_sociales', []),
                calle          = form.cleaned_data.get('calle', ''),
                numero         = form.cleaned_data.get('numero', ''),
                piso_depto     = form.cleaned_data.get('piso_depto', ''),
                telefono_consultorio = form.cleaned_data.get('telefono_consultorio', ''),
                ciudad_consultorio   = form.cleaned_data.get('ciudad_consultorio'),
                )
                login(request, usuario)
                return redirect('home_principal')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = RegistroMedicoForm()

    return render(request, 'registro_medico.html', {'form': form})

def registro_paciente(request):
    if request.user.is_authenticated:
        return redirect('home_principal')

    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            try:
                Registro.validar_unicidad(dni=form.cleaned_data['dni'])
                usuario = Registro.registrar_usuario(form)
                Registro.registrar_paciente(
                    usuario     = usuario,
                    dni         = form.cleaned_data['dni'],
                    telefono    = form.cleaned_data.get('telefono', ''),
                    obra_social = form.cleaned_data.get('obra_social'),
                )
                login(request, usuario)
                return redirect('home_principal')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = RegistroPacienteForm()

    return render(request, 'registro_paciente.html', {'form': form})

# Metodos de visitante 

def busqueda_publica(request):
    # Si llega con parámetros (GET o POST), redirigir a resultados públicos
    if request.method == 'GET' and request.GET:
        especialidad = request.GET.get('especialidad', '').strip()
        obra_social  = request.GET.get('obra_social', '').strip()
        nombre       = request.GET.get('nombre', '').strip()
        return redirect(
            f"/resultados-publicos/?especialidad={especialidad}"
            f"&obra_social={obra_social}&nombre={nombre}"
        )
    # Si es POST (por si se usa desde otro formulario), también funciona
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad', '').strip()
        ciudad       = request.POST.get('ciudad', '').strip()
        obra_social  = request.POST.get('obra_social', '').strip()
        nombre       = request.POST.get('nombre', '').strip()
        return redirect(
            f"/resultados-publicos/?especialidad={especialidad}"
            f"&ciudad={ciudad}&obra_social={obra_social}&nombre={nombre}"
        )
    # Si no hay parámetros, mostrar el formulario de búsqueda (poco probable desde el home)
    return render(request, 'paciente/buscar_turnos.html', {
        'especialidades': Especialidad.objects.all(),
        'ciudades':       Ciudad.objects.all(),
        'obras_sociales': ObraSocial.objects.all(),
    })

def resultados_publicos(request):
    from django.core.paginator import Paginator
    from gestion_turnos.servicios.gestor_busqueda import GestorBusqueda

    especialidad = request.GET.get('especialidad', '')
    ciudad       = request.GET.get('ciudad', '')
    obra_social  = request.GET.get('obra_social', '')
    nombre       = request.GET.get('nombre', '')

    medicos = GestorBusqueda.buscar_medicos(
        especialidad, nombre=nombre, ciudad=ciudad, obra_social=obra_social
    )
    paginator = Paginator(medicos, 5)
    pagina    = paginator.get_page(request.GET.get('page'))

    return render(request, 'paciente/resultados_busqueda.html', {
        'medicos':      pagina,
        'especialidad': especialidad,
        'ciudad':       ciudad,
        'obra_social':  obra_social,
        'nombre':       nombre,
    })

def detalle_medico_publico(request, medico_id):
    from gestion_turnos.models import Medico
    from gestion_turnos.servicios.gestor_busqueda import GestorBusqueda

    medico = GestorBusqueda.obtener_perfil_medico(medico_id)
    turnos_por_fecha = GestorBusqueda.obtener_turnos_disponibles(medico_id)

    # Navegación semanal (igual que en detalle_medico del paciente)
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_inicio = date.fromisoformat(fecha_str)
        except ValueError:
            fecha_inicio = date.today()
    else:
        fecha_inicio = date.today()

    fecha_fin = fecha_inicio + timedelta(days=6)
    semana_anterior = fecha_inicio - timedelta(weeks=1)
    semana_siguiente = fecha_inicio + timedelta(weeks=1)
    dias_semana = [fecha_inicio + timedelta(days=i) for i in range(7)]

    return render(request, 'paciente/detalle_medico.html', {
        'medico':           medico,
        'turnos_por_fecha': turnos_por_fecha,
        'dias_semana':      dias_semana,
        'fecha_inicio':     fecha_inicio,
        'semana_anterior':  semana_anterior,
        'semana_siguiente': semana_siguiente,
        'today':            date.today(),
    })