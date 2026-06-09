from gestion_turnos.models import Medico

def resolver_destino_usuario(user):
    """
    Determina a dónde redirigir según el rol del usuario.
    Devuelve tupla (ruta, kwargs).
    """
    if user.is_superuser or user.is_staff:
        return ('/admin/', {})

    try:
        medico = Medico.objects.get(user=user)
        return ('agenda_semanal', {'medico_id': medico.id})
    except Medico.DoesNotExist:
        return ('dashboard_paciente', {})