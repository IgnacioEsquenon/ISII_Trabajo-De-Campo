from django.core.exceptions import ValidationError
from gestion_turnos.models import Turno, Reserva

class GestorReserva:
    """
    Fachada de reserva. Centraliza la lógica de reservar
    y cancelar turnos desde la perspectiva del paciente.
    """

    def reservar_turno(self, paciente, turno, motivo_consulta=''):
        """
        Crea una reserva para el paciente en el turno indicado.
        Valida disponibilidad, bloquea el turno y genera el código.
        Devuelve la reserva creada.
        """
        if not turno.esta_disponible():
            raise ValidationError('El turno ya no está disponible.')

        # Creamos la reserva — el código se genera en save()
        reserva = Reserva.objects.create(
            turno           = turno,
            paciente        = paciente,
            motivo_consulta = motivo_consulta,
        )

        # Bloqueamos el turno
        turno.bloquear()

        return reserva

    def cancelar_reserva(self, reserva):
        """
        Cancela la reserva si cumple la regla de las 24hs.
        Delega la validación al método del modelo.
        """
        if not reserva.es_cancelable():
            raise ValidationError(
                'No podés cancelar un turno con menos de 24hs de anticipación.'
            )
        # Delegamos cancelar al modelo — él libera el turno
        reserva.cancelar()