from django.urls import path
from gestion_turnos.views.medico import agenda_medico, eliminar_bloque

urlpatterns = [
    path('medico/<int:medico_id>/agenda/',          agenda_medico,   name='agenda_medico'),
    path('medico/bloque/<int:bloque_id>/eliminar/', eliminar_bloque, name='eliminar_bloque'),
]