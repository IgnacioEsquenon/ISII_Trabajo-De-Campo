
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from gestion_turnos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registro/', views.seleccionar_registro, name='seleccionar_registro'),
    path('registro/medico/', views.registro_medico, name='registro_medico'),
    path('registro/paciente/', views.registro_paciente, name='registro_paciente'),
    path('login/',  auth_views.LoginView.as_view(template_name='login.html'),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('',include('gestion_turnos.urls')),
]
