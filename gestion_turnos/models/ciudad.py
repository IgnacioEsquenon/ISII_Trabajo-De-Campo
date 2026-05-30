from django.db import models
from .provincia import Provincia

class Ciudad(models.Model):
    nombre   = models.CharField(max_length=100)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='ciudades'
    )

    def __str__(self):
        return f"{self.nombre}, {self.provincia}"

    class Meta:
        ordering = ['nombre']

    @staticmethod
    def listar():
        return Ciudad.objects.all()

    def obtener_clinicas(self):
        return self.clinicas.all()