from gestion_turnos.models import Medico, Paciente

def resolver_destino_usuario(user):
    if user.is_superuser or user.is_staff:
        return ('/admin/', {})
    
    try:
        medico = Medico.objects.get(user=user)
        return ('agenda_medico', {'medico_id': medico.id})
    except Medico.DoesNotExist:
        return ('home_paciente', {})

def registrar_medico(form):
    user = form.save(commit=False)
    user.first_name = form.cleaned_data['nombre']
    user.last_name  = form.cleaned_data['apellido']
    user.save()

    medico = Medico.objects.create(
        user         = user,
        nombre       = f"{form.cleaned_data['nombre']} {form.cleaned_data['apellido']}",
        especialidad = form.cleaned_data['especialidad'],
        matricula    = form.cleaned_data['matricula']
    )

    # Muchos a muchos se asigna después del save()
    medico.obras_sociales.set(form.cleaned_data['obras_sociales'])
    return user

def registrar_paciente(form):
    user = form.save(commit=False)
    user.first_name = form.cleaned_data['nombre']
    user.last_name  = form.cleaned_data['apellido']
    user.save()

    Paciente.objects.create(
        user     = user,
        nombre   = form.cleaned_data['nombre'],
        apellido = form.cleaned_data['apellido'],
        dni      = form.cleaned_data['dni'],
        telefono = form.cleaned_data['telefono']
    )
    return user