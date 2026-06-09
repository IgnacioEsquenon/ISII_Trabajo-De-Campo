from django.db import models
from .bloque import BloqueHorario
from datetime import time
from django.core.exceptions import ValidationError

class Turno(models.Model):
    bloque         = models.ForeignKey(BloqueHorario, on_delete=models.CASCADE, related_name='turnos')
    fecha          = models.DateField()
    hora_inicio    = models.TimeField(default=time(0, 0))       # ← antes era 'hora'
    hora_fin       = models.TimeField(default=time(0, 0))       # ← nuevo
    esta_reservado = models.BooleanField(default=False)   # ← reemplaza estado
    esta_activo    = models.BooleanField(default=True)    # ← nuevo

    class Meta:
        unique_together = ['bloque', 'fecha', 'hora_inicio']

    def __str__(self):
        estado = 'Reservado' if self.esta_reservado else 'Disponible'
        return f"{self.fecha} {self.hora_inicio} — {estado}"

    def bloquear(self):
        filas_afectadas = Turno.objects.filter(
            id=self.id,
            esta_reservado=False,
            esta_activo=True
        ).update(esta_reservado=True)
        
        if filas_afectadas == 0:
            return False
        
        self.refresh_from_db()
        return True

    def liberar(self):
        #Libera el turno para que vuelva a estar disponible.
        if not self.esta_reservado:
            raise ValidationError("El turno no está reservado.")
        self.esta_reservado = False
        self.save()

    def desactivar(self):
        #Desactiva el turno para que no sea visible ni reservable.
        if self.esta_activo:
            self.esta_activo = False
            self.save()

    def esta_disponible(self):
        #Devuelve True si el turno puede ser reservado.
        return not self.esta_reservado and self.esta_activo