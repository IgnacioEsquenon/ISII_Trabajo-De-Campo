from django.db import models

class Provincia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

    @staticmethod
    def listar():
        return Provincia.objects.all()

    def obtener_ciudades(self):
        return self.ciudades.all()