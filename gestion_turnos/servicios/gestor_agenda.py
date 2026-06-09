from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from gestion_turnos.models import BloqueHorario, Turno

class GestorAgenda:
    """
    Fachada de agenda. Gestiona la creación, edición y eliminación
    de bloques horarios y la generación automática de turnos.
    """

    def __init__(self, medico):
        self.medico = medico

    def obtener_estructura_bloques(self):
        """
        Devuelve los bloques activos del médico agrupados por día.
        Usado para renderizar la agenda.
        """
        bloques_por_dia = {}
        for b in BloqueHorario.obtener_bloques_activos(self.medico):
            dia = b.obtener_nombre_dia()
            bloques_por_dia.setdefault(dia, []).append(b)
        return bloques_por_dia

    def crear_bloque_horario(self, dia_semana, hora_inicio, hora_fin, duracion_turno, semanas=4):
        """
        Crea un bloque horario y genera sus turnos automáticamente.
        Valida superposición antes de guardar.
        Devuelve el bloque creado.
        """
        bloque = BloqueHorario(
            medico         = self.medico,
            dia_semana     = dia_semana,
            hora_inicio    = hora_inicio,
            hora_fin       = hora_fin,
            duracion_turno = duracion_turno,
        )

        # Validaciones del modelo (hora_inicio < hora_fin, duración mínima)
        bloque.full_clean()

        # Validación de superposición usando el método del modelo, solo para el mismo día
        bloques_mismo_dia = BloqueHorario.obtener_bloques_activos(self.medico).filter(
            dia_semana=bloque.dia_semana
        )
        for b in bloques_mismo_dia:
            if bloque.validar_superposicion(b):
                raise ValidationError(
                    f"Se superpone con bloque existente: "
                    f"{b.hora_inicio.strftime('%H:%M')} a {b.hora_fin.strftime('%H:%M')}."
                )

        bloque.save()
        bloque.generar_turnos(semanas)
        return bloque

    def eliminar_bloque_horario(self, bloque):
        bloque.desactivar()

    def editar_bloque_horario(self, bloque, dia_semana, hora_inicio, hora_fin, duracion_turno, semanas=4):
        self.eliminar_bloque_horario(bloque)
        return self.crear_bloque_horario(dia_semana, hora_inicio, hora_fin, duracion_turno, semanas)
