from django.urls import path
from gestion_turnos.views.auth import home_principal, seleccionar_registro, registro_medico, registro_paciente, busqueda_publica, resultados_publicos, detalle_medico_publico 

urlpatterns = [
    path('',                       home_principal,       name='home_principal'),
    path('registro/',              seleccionar_registro, name='seleccionar_registro'),
    path('registro/medico/',       registro_medico,      name='registro_medico'),
    path('registro/paciente/',     registro_paciente,    name='registro_paciente'),
    path('resultados-publicos/', resultados_publicos, name='resultados_publicos'),
    path('busqueda-publica/', busqueda_publica, name='busqueda_publica'),
    path('medico-publico/<int:medico_id>/turnos/', detalle_medico_publico, name='detalle_medico_publico'),
]