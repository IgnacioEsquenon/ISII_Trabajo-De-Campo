from django.db import models

class ConsultorioParticular(models.Model):
    """
    Dirección del consultorio de un médico que atiende de forma particular.
    Se crea al registrarse si el médico no pertenece a ninguna clínica.
    """
    medico     = models.OneToOneField(
        'Medico',
        on_delete    = models.CASCADE,
        related_name = 'consultorio_particular'
    )
    calle      = models.CharField(max_length=100)
    numero     = models.CharField(max_length=20)
    piso_depto = models.CharField(max_length=30, blank=True)
    telefono   = models.CharField(max_length=25, blank=True)
    ciudad     = models.ForeignKey(        # ← nuevo
        'Ciudad',
        on_delete    = models.SET_NULL,
        null=True, blank=True,
        related_name = 'consultorios'
    )

    def __str__(self):
        return f"Consultorio de {self.medico.nombre}"

    def get_direccion_completa(self):
        """Devuelve la dirección formateada como string."""
        base = f"{self.calle} {self.numero}"
        if self.piso_depto:
            base += f", {self.piso_depto}"
        if self.ciudad:
            base += f" — {self.ciudad}"  # muestra "ciudad, provincia"
        return base