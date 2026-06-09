from django.urls import path
from gestion_turnos.views.medico import eliminar_bloque, editar_bloque, agenda_semanal, configurar_bloques, historial_medico, confirmar_atencion

urlpatterns = [
    path('medico/<int:medico_id>/agenda/',  agenda_semanal,      name='agenda_semanal'),
    path('medico/<int:medico_id>/bloques/',   configurar_bloques,  name='configurar_bloques'),
    path('medico/<int:medico_id>/historial/', historial_medico,    name='historial_medico'),
    path('medico/bloque/<int:bloque_id>/eliminar/', eliminar_bloque, name='eliminar_bloque'),
    path('medico/bloque/<int:bloque_id>/editar/',   editar_bloque,   name='editar_bloque'),
    path('confirmar-atencion/<int:reserva_id>/', confirmar_atencion, name='confirmar_atencion'),
]