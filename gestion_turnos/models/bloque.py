from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
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

    medico               = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='bloques')
    dia_semana           = models.IntegerField(choices=DIAS)
    hora_inicio          = models.TimeField()
    hora_fin             = models.TimeField()
    duracion_turno       = models.IntegerField(choices=DURACIONES, default=30)
    activo               = models.BooleanField(default=True)          # ← nuevo
    ultimo_turno_generado = models.DateField(null=True, blank=True)   # ← nuevo

    class Meta:
        ordering        = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.obtener_nombre_dia()} {self.hora_inicio}–{self.hora_fin}"

    def clean(self):
        #Validaciones lógicas puras, sin tocar DB
        if self.hora_inicio and self.hora_fin:
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

            inicio_dt       = datetime.combine(date.today(), self.hora_inicio)
            fin_dt          = datetime.combine(date.today(), self.hora_fin)
            minutos_totales = (fin_dt - inicio_dt).total_seconds() / 60

            if minutos_totales < self.duracion_turno:
                raise ValidationError(
                    f"El bloque dura {int(minutos_totales)} min "
                    f"pero elegiste turnos de {self.duracion_turno} min."
                )

    def obtener_nombre_dia(self):
        return dict(self.DIAS).get(self.dia_semana, '')

    def generar_turnos(self, semanas):
        from .turno import Turno
        hoy = date.today()
        dias_hasta = (self.dia_semana - hoy.weekday()) % 7
        proxima_fecha = hoy + timedelta(days=dias_hasta)
        turnos_creados = []

        for semana in range(1, semanas + 1):
            fecha_turno = proxima_fecha + timedelta(weeks=semana - 1)
            hora_actual = self.hora_inicio
            while (datetime.combine(fecha_turno, hora_actual) + timedelta(minutes=self.duracion_turno)).time() <= self.hora_fin:
                hora_fin_turno = (datetime.combine(fecha_turno, hora_actual) + timedelta(minutes=self.duracion_turno)).time()

                existe_reservado = Turno.objects.filter(
                    bloque__medico=self.medico,
                    fecha=fecha_turno,
                    hora_inicio=hora_actual,
                    esta_reservado=True
                ).exists()
                existe_mismo_bloque = Turno.objects.filter(
                    bloque=self,
                    fecha=fecha_turno,
                    hora_inicio=hora_actual
                ).exists()

                if not existe_reservado and not existe_mismo_bloque:
                    turno = Turno.objects.create(
                        bloque=self,
                        fecha=fecha_turno,
                        hora_inicio=hora_actual,
                        hora_fin=hora_fin_turno,
                        esta_activo=True,
                        esta_reservado=False
                    )
                    turnos_creados.append(turno)

                hora_actual = (datetime.combine(fecha_turno, hora_actual) + timedelta(minutes=self.duracion_turno)).time()

        if turnos_creados:
            self.ultimo_turno_generado = max(t.fecha for t in turnos_creados)
            self.save(update_fields=['ultimo_turno_generado'])
        return turnos_creados
    
    def validar_superposicion(self, otro_bloque):
        return self.hora_inicio < otro_bloque.hora_fin and self.hora_fin > otro_bloque.hora_inicio

    def desactivar(self):
        #Eliminación lógica del bloque.
        self.activo = False
        self.save()
        for turno in self.turnos.all():
            turno.desactivar()

    def obtener_turnos_disponibles(self):
        ahora = datetime.now()
        return self.turnos.filter(
            esta_reservado=False,
            esta_activo=True
        ).exclude(
            fecha=date.today(),
            hora_inicio__lt=ahora.time()
        ).filter(
            fecha__gte=date.today()
        ).order_by('fecha', 'hora_inicio')

    def obtener_turnos(self):
        #Devuelve todos los turnos futuros de este bloque.
        return self.turnos.filter(
            fecha__gte  = date.today(),
            esta_activo = True
        ).order_by('fecha', 'hora_inicio')

    @staticmethod
    def obtener_bloques_activos(medico):
        return BloqueHorario.objects.filter(medico=medico, activo=True)