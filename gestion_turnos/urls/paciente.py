from django.urls import path
from gestion_turnos.views.paciente import autocomplete_medico
from gestion_turnos.views.paciente import (
    dashboard_paciente,
    buscar_turnos,
    resultados_busqueda,
    detalle_medico,
    confirmar_turno,
    reserva_exitosa,
    mis_turnos,
    cancelar_turno,
    perfil_paciente,
)

urlpatterns = [
    path('paciente/',                              dashboard_paciente, name='dashboard_paciente'),
    path('paciente/buscar/',                       buscar_turnos,      name='buscar_turnos'),
    path('paciente/resultados/',                   resultados_busqueda, name='resultados_busqueda'),
    path('paciente/medico/<int:medico_id>/turnos/', detalle_medico,    name='detalle_medico'),
    path('paciente/turno/<int:turno_id>/confirmar/', confirmar_turno,  name='confirmar_turno'),
    path('paciente/reserva/<int:reserva_id>/exitosa/', reserva_exitosa, name='reserva_exitosa'),
    path('paciente/autocomplete/medico/',           autocomplete_medico, name='autocomplete_medico'),
    path('paciente/mis-turnos/',                   mis_turnos,         name='mis_turnos'),
    path('paciente/reserva/<int:reserva_id>/cancelar/', cancelar_turno, name='cancelar_turno'),
    path('paciente/perfil/',                       perfil_paciente,    name='perfil_paciente'),
]