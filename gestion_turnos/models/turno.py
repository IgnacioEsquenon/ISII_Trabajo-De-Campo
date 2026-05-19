from django.db import models
from .bloque   import BloqueHorario
from .paciente import Paciente

class Turno(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('reservado',  'Reservado'),
        ('cancelado',  'Cancelado'),
    ]
    bloque   = models.ForeignKey(BloqueHorario, on_delete=models.CASCADE, related_name='turnos')
    paciente = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True)
    fecha    = models.DateField()
    hora     = models.TimeField()
    estado   = models.CharField(max_length=20, choices=ESTADOS, default='disponible')

    class Meta:
        unique_together = ['bloque', 'fecha', 'hora']

    def __str__(self):
        return f"{self.fecha} {self.hora} — {self.get_estado_display()}"

    # Si en el futuro necesitás lógica como reservar o cancelar,
    # solo propiedades o validaciones simples van acá:
    
    @property
    def esta_disponible(self):
        return self.estado == 'disponible'