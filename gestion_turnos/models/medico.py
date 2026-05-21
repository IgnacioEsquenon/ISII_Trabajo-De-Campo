from django.db import models
from django.contrib.auth.models import User
from .especialidad import Especialidad
from .obra_social import ObraSocial

class Medico(models.Model):
    user         = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre       = models.CharField(max_length=100)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True)  #antes era texto 
    matricula    = models.CharField(max_length=50, unique=True)
    obras_sociales = models.ManyToManyField(ObraSocial, blank=True)  # ← muchos a muchos

    def __str__(self):
        return f"Dr. {self.nombre} ({self.especialidad})"