from django.db import models
from .ciudad import Ciudad

class Clinica(models.Model):
    nombre       = models.CharField(max_length=150)
    calle        = models.CharField(max_length=100)
    numero       = models.CharField(max_length=20)
    piso_depto   = models.CharField(max_length=30, blank=True)
    telefono     = models.CharField(max_length=25, blank=True)
    ciudad       = models.ForeignKey(
        Ciudad,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clinicas'
    )

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

    def get_direccion_completa(self):
        """Devuelve la dirección formateada como string."""
        base = f"{self.calle} {self.numero}"
        if self.piso_depto:
            base += f", {self.piso_depto}"
        if self.ciudad:
            base += f" — {self.ciudad}"
        return base

    @staticmethod
    def listar():
        return Clinica.objects.all()