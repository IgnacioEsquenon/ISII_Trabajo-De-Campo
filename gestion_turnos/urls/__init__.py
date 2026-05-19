from django.urls import path, include

urlpatterns = [
    path('', include('gestion_turnos.urls.auth')),
    path('', include('gestion_turnos.urls.medico')),
    path('', include('gestion_turnos.urls.paciente')),
]