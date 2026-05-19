from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, date
from .medico import Medico 

class BloqueHorario(models.Model):
    DIAS = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    DURACIONES = [
        (30, '30 minutos'),
        (60, '60 minutos'),
    ]

    medico         = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='bloques')
    dia_semana     = models.IntegerField(choices=DIAS)
    hora_inicio    = models.TimeField()
    hora_fin       = models.TimeField()
    duracion_turno = models.IntegerField(choices=DURACIONES, default=30)

    class Meta:
        ordering        = ['dia_semana', 'hora_inicio']
        unique_together = ['medico', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio}–{self.hora_fin}"

    def clean(self):
        # Solo las validaciones lógicas puras, sin tocar DB
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

            inicio_dt      = datetime.combine(date.today(), self.hora_inicio)
            fin_dt         = datetime.combine(date.today(), self.hora_fin)
            minutos_totales = (fin_dt - inicio_dt).total_seconds() / 60

            if minutos_totales < self.duracion_turno:
                raise ValidationError(f"El bloque dura {int(minutos_totales)} min pero elegiste turnos de {self.duracion_turno} min.")

        # La validación de superposición se va al service