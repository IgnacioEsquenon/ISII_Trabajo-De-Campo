from django.db import models

class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    siglas = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

    @staticmethod
    def listar():
        return ObraSocial.objects.all()