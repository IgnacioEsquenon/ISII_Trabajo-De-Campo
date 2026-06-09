from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from .turno import Turno
from .paciente import Paciente

class Reserva(models.Model):
    ESTADOS = [
        ('activa',    'Activa'),
        ('cancelada', 'Cancelada'),
        ('atendida',  'Atendida'),   
    ]

    turno           = models.OneToOneField(Turno, on_delete=models.CASCADE, related_name='reserva')
    paciente        = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='reservas')
    codigo_reserva  = models.CharField(max_length=20, unique=True, editable=False)
    estado          = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    diagnostico     = models.TextField(blank=True)       # ← nuevo
    motivo_consulta = models.TextField(blank=True)       # ← nuevo
    created_at      = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generamos el código automáticamente si no existe
        if not self.codigo_reserva:
            self.codigo_reserva = f"RES-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo_reserva} — {self.paciente} — {self.turno}"

    def cancelar(self):
        if self.estado != 'activa':
            raise ValidationError("Solo se pueden cancelar reservas activas.")
        self.estado = 'cancelada'
        self.save()
        self.turno.liberar()

    def confirmar_atencion(self, diagnostico):
        #Marca la reserva como atendida y guarda el diagnóstico.
        if self.estado != 'activa':
            raise ValidationError("Solo se puede confirmar atención de una reserva activa.")
        self.estado      = 'atendida'
        self.diagnostico = diagnostico
        self.save()

    def es_cancelable(self):
        #Devuelve True si faltan más de 24hs para el turno.
        if self.estado != 'activa':
            return False
        ahora       = timezone.now()
        fecha_turno = datetime.combine(self.turno.fecha, self.turno.hora_inicio)
        fecha_turno = timezone.make_aware(fecha_turno)
        return (fecha_turno - ahora) > timedelta(hours=24)

    def horas_hasta_el_turno(self):
        #Devuelve las horas que faltan hasta el turno como float.
        ahora       = timezone.now()
        fecha_turno = datetime.combine(self.turno.fecha, self.turno.hora_inicio)
        fecha_turno = timezone.make_aware(fecha_turno)
        diferencia  = fecha_turno - ahora
        return diferencia.total_seconds() / 3600