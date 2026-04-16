from django.urls import path

from gestion_turnos.models import Medico
from . import views
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required


def home(request):
    # Si no hay nadie logueado, pal login 
    if not request.user.is_authenticated:
        return redirect('login')

    # Si es admin/superusuario, al panel del admin
    # is_superuser y is_staff son propiedades nativas de Django para los admin
    if request.user.is_superuser or request.user.is_staff:
        return redirect('/admin/') 

    # Si no es admin, averiguamos si es un Médico
    try:
        medico = Medico.objects.get(user=request.user)
        # Si es un médico, lo mandamos a su agenda
        return redirect('agenda_medico', medico_id=medico.id)
        
    except Medico.DoesNotExist:
        # Si no es admin y no es medico, asumimos que es un paciente (en un sistema real habría que validar esto mejor pero bueno xd)
        # Acá después lo mandaremos a la vista de reservar turnos. Como no hay nada implementado, por ahora lo mandamos a una página de bienvenida.
        return render(request, 'home_paciente.html', {'mensaje': 'Bienvenido al portal del paciente'})

urlpatterns = [
    path('', home, name='home'),
    path('medico/<int:medico_id>/agenda/', views.agenda_medico,    name='agenda_medico'),
    path('bloque/<int:bloque_id>/toggle/', views.toggle_bloque,    name='toggle_bloque'),
    path('bloque/<int:bloque_id>/eliminar/', views.eliminar_bloque, name='eliminar_bloque'),
]