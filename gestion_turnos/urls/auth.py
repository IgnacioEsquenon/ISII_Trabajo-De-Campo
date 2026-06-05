from django.urls import path
from gestion_turnos.views.auth import home_principal, seleccionar_registro, registro_medico, registro_paciente, busqueda_publica, detalle_medico_publico 

urlpatterns = [
    path('',                       home_principal,       name='home_principal'),
    path('registro/',              seleccionar_registro, name='seleccionar_registro'),
    path('registro/medico/',       registro_medico,      name='registro_medico'),
    path('registro/paciente/',     registro_paciente,    name='registro_paciente'),
    path('busqueda/',              busqueda_publica,     name='busqueda_publica'),
    path('medico/<int:medico_id>/', detalle_medico_publico, name='detalle_medico_publico'),
]