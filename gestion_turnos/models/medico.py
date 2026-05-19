from django.db import models
from django.contrib.auth.models import User

class Medico(models.Model):    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    matricula = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Dr. {self.nombre} ({self.especialidad})"