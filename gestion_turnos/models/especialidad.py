from django.db import models

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, default='')
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

    @staticmethod
    def listar():
        return Especialidad.objects.all()