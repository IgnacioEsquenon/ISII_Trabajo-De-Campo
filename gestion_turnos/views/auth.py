from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from gestion_turnos.forms import RegistroMedicoForm, RegistroPacienteForm
from gestion_turnos.servicios.usuarios import resolver_destino_usuario
from gestion_turnos.servicios.registro import Registro

def home_principal(request):
    if not request.user.is_authenticated:
        return render(request, 'home_principal.html')
    ruta, kwargs = resolver_destino_usuario(request.user)
    return redirect(ruta, **kwargs)

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