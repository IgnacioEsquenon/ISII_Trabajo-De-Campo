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
        for b in self.medico.bloques.filter(activo=True):
            dia = b.get_dia_semana_display()
            bloques_por_dia.setdefault(dia, []).append(b)
        return bloques_por_dia

    def obtener_bloques(self):
        """Devuelve todos los bloques activos del médico."""
        return self.medico.bloques.filter(activo=True)

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

        # Validación de superposición con bloques existentes
        self._validar_superposicion(bloque)

        bloque.save()

        # Generamos los turnos automáticamente
        turnos = self._generar_turnos(bloque, semanas)
        self._guardar_turnos(bloque, turnos)

        return bloque

    def eliminar_bloque_horario(self, bloque):
        """
        Eliminación lógica del bloque.
        Desactiva el bloque y borra solo los turnos disponibles futuros.
        Si tiene turnos reservados activos lanza ValidationError.
        """
        tiene_reservados = Turno.objects.filter(
            bloque         = bloque,
            esta_reservado = True,
            fecha__gte     = date.today()
        ).exists()

        if tiene_reservados:
            raise ValidationError(
                'No podés eliminar este bloque porque tiene turnos reservados activos.'
            )

        # Eliminación lógica
        bloque.desactivar()

        # Borramos solo los disponibles futuros
        Turno.objects.filter(
            bloque         = bloque,
            fecha__gte     = date.today(),
            esta_reservado = False
        ).delete()

    def editar_bloque_horario(self, bloque, dia_semana, hora_inicio, hora_fin, duracion_turno, semanas=4):
        """
        Actualiza un bloque existente y regenera sus turnos
        respetando los ya reservados.
        """
        bloque.dia_semana     = dia_semana
        bloque.hora_inicio    = hora_inicio
        bloque.hora_fin       = hora_fin
        bloque.duracion_turno = duracion_turno

        bloque.full_clean()
        self._validar_superposicion(bloque)
        bloque.save()

        # Borramos solo los disponibles futuros
        Turno.objects.filter(
            bloque         = bloque,
            fecha__gte     = date.today(),
            esta_reservado = False
        ).delete()

        # Regeneramos respetando los reservados
        turnos = self._generar_turnos(bloque, semanas)
        self._guardar_turnos(bloque, turnos)

        return bloque

    # ── Métodos privados ──────────────────────────────────────────

    def _validar_superposicion(self, bloque):
        """Verifica que el bloque no se superponga con otros del mismo médico."""
        bloques_existentes = BloqueHorario.objects.filter(
            medico_id  = self.medico.id,
            dia_semana = bloque.dia_semana,
            activo     = True
        )
        if bloque.pk:
            bloques_existentes = bloques_existentes.exclude(pk=bloque.pk)

        for b in bloques_existentes:
            if bloque.hora_inicio < b.hora_fin and bloque.hora_fin > b.hora_inicio:
                raise ValidationError(
                    f"Se superpone con bloque existente: "
                    f"{b.hora_inicio.strftime('%H:%M')} a {b.hora_fin.strftime('%H:%M')}."
                )

    def _generar_turnos(self, bloque, semanas=4):
        """
        Genera la lista de dicts con los turnos del bloque para N semanas.
        No toca la DB.
        """
        hoy               = date.today()
        dias_para_proximo = (bloque.dia_semana - hoy.weekday()) % 7
        proxima_fecha     = hoy + timedelta(days=dias_para_proximo)
        fechas            = [proxima_fecha + timedelta(weeks=i) for i in range(semanas)]

        inicio_dt = datetime.combine(hoy, bloque.hora_inicio)
        fin_dt    = datetime.combine(hoy, bloque.hora_fin)
        turnos    = []

        for fecha in fechas:
            actual = inicio_dt
            while (actual + timedelta(minutes=bloque.duracion_turno)) <= fin_dt:
                fin_turno = actual + timedelta(minutes=bloque.duracion_turno)
                turnos.append({
                    'fecha':          fecha,
                    'hora_inicio':    actual.time(),
                    'hora_fin':       fin_turno.time(),
                    'esta_reservado': False,
                    'esta_activo':    True,
                })
                actual += timedelta(minutes=bloque.duracion_turno)

        return turnos

    def _guardar_turnos(self, bloque, turnos_data):
        """
        Persiste los turnos en la DB.
        Filtra las franjas ya reservadas para no generar duplicados.
        """
        # Franjas ya reservadas del médico para no pisarlas
        reservados = {
            (t.fecha, t.hora_inicio)
            for t in Turno.objects.filter(
                bloque__medico = self.medico,
                esta_reservado = True,
                fecha__gte     = date.today()
            )
        }

        objetos = [
            Turno(bloque=bloque, **t)
            for t in turnos_data
            if (t['fecha'], t['hora_inicio']) not in reservados
        ]

        if objetos:
            Turno.objects.bulk_create(objetos)

            # Actualizamos la fecha del último turno generado
            bloque.ultimo_turno_generado = max(t.fecha for t in objetos)
            bloque.save(update_fields=['ultimo_turno_generado'])