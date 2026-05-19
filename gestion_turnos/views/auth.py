from django.shortcuts import render, redirect
from django.contrib.auth import login
from gestion_turnos.forms import RegistroMedicoForm, RegistroPacienteForm
from gestion_turnos.servicios.usuarios import registrar_medico, registrar_paciente, resolver_destino_usuario

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
            user = registrar_medico(form)
            login(request, user)
            return redirect('home_principal')
    else:
        form = RegistroMedicoForm()

    return render(request, 'registro_medico.html', {'form': form})

def registro_paciente(request):
    if request.user.is_authenticated:
        return redirect('home_principal')

    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = registrar_paciente(form)
            login(request, user)
            return redirect('home_principal')
    else:
        form = RegistroPacienteForm()

    return render(request, 'registro_paciente.html', {'form': form})