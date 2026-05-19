from django.urls import path
from gestion_turnos.views.paciente import home_paciente

urlpatterns = [
    path('paciente/', home_paciente, name='home_paciente'),
]