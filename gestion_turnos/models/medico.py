from django.db import models
from django.contrib.auth.models import User
from .especialidad import Especialidad
from .obra_social import ObraSocial

class Medico(models.Model):
    ESTADOS = [
        ('pendiente',  'Pendiente'),
        ('aprobado',   'Aprobado'),
        ('rechazado',  'Rechazado'),
    ]

    user           = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nombre         = models.CharField(max_length=100)
    especialidad   = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True)
    matricula      = models.CharField(max_length=50, unique=True)
    obras_sociales = models.ManyToManyField(ObraSocial, blank=True)
    estado         = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')  # ← nuevo

    # Un médico atiende en una clínica O de forma particular
    clinica        = models.ForeignKey(
        'Clinica',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medicos'
    )
    es_particular  = models.BooleanField(default=False)  # ← nuevo

    def __str__(self):
        return f"Dr. {self.nombre} ({self.especialidad})"

    def aprobar(self):
        self.estado = 'aprobado'
        self.save()

    def rechazar(self):
        self.estado = 'rechazado'
        self.save()

    def esta_aprobado(self):
        return self.estado == 'aprobado'

    def actualizar_datos(self, especialidad, clinica, obras_sociales):
        """Actualiza los datos profesionales del médico."""
        self.especialidad = especialidad
        self.clinica      = clinica
        self.save()
        self.obras_sociales.set(obras_sociales)

    @staticmethod
    def existe_por_matricula(matricula):
        return Medico.objects.filter(matricula=matricula).exists()
    
def get_lugar_atencion(self):
    """Devuelve la dirección donde atiende, sea clínica o consultorio."""
    if self.clinica:
        return self.clinica.get_direccion_completa()
    if self.es_particular and hasattr(self, 'consultorio_particular'):
        return self.consultorio_particular.get_direccion_completa()
    return 'Sin dirección registrada'