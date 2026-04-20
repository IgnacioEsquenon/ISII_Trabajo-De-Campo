from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# creamos los modelos para la app de gestión de turnos (en python las clases son modelos quien lo diria)
# a su vez, cada clase representa una tabla en la base de datos
# django es el que crea dichas tablas

class Medico(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    matricula = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Dr. {self.nombre} ({self.especialidad})"

class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"
    
class BloqueHorario(models.Model):
    DIAS = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    DURACIONES = [
        (30, '30 minutos'),
        (60, '60 minutos'),
    ]

    medico      = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='bloques')
    dia_semana  = models.IntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    duracion_turno = models.IntegerField(choices=DURACIONES, default=30)
    #activo      = models.BooleanField(default=True)

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['medico', 'dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio}–{self.hora_fin}" 
    
    def clean(self):
        super().clean() 

        # 1. Validación Lógica (Esta se puede hacer siempre porque usa los datos del formulario)
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

            # 2. Validación de Superposición (Requisito T1-08)
            if self.medico_id is not None:
                bloques_existentes = BloqueHorario.objects.filter(
                    medico_id=self.medico_id, 
                    dia_semana=self.dia_semana
                )
                
                if self.pk:
                    bloques_existentes = bloques_existentes.exclude(pk=self.pk)

                for bloque in bloques_existentes:
                    if self.hora_inicio < bloque.hora_fin and self.hora_fin > bloque.hora_inicio:
                        raise ValidationError(f"El horario se superpone con un bloque existente: {bloque.hora_inicio.strftime('%H:%M')} a {bloque.hora_fin.strftime('%H:%M')}.")

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
    

