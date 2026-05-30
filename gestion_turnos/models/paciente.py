from django.db import models
from django.contrib.auth.models import User
from .obra_social import ObraSocial

class Paciente(models.Model):
    user       = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre     = models.CharField(max_length=100)
    apellido   = models.CharField(max_length=100)
    dni        = models.CharField(max_length=20, unique=True)
    telefono   = models.CharField(max_length=20, blank=True, null=True)
    obra_social = models.ForeignKey(          # ← nuevo
        ObraSocial,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pacientes'
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def actualizar_datos(self, telefono, obra_social):
        """Actualiza los datos del paciente."""
        self.telefono    = telefono
        self.obra_social = obra_social
        self.save()