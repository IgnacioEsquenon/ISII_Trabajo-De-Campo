from django.db import models
from django.contrib.auth.models import User 

class Paciente(models.Model):
    user     = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre   = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni      = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"