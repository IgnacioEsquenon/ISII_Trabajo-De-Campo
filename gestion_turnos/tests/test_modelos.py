from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta, datetime
from django.utils import timezone
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Paciente, BloqueHorario, Turno, Reserva, Especialidad
)


class TestTurno(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico9', password='1234')
        medico       = Medico.objects.create(
            user=user, nombre='García', matricula='M009',
            especialidad=especialidad, estado='aprobado'
        )
        bloque       = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        self.turno   = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )

    def test_bloquear(self):
        self.turno.bloquear()
        self.turno.refresh_from_db()
        self.assertTrue(self.turno.esta_reservado)

    def test_liberar(self):
        self.turno.bloquear()
        self.turno.liberar()
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_reservado)

    def test_desactivar(self):
        self.turno.desactivar()
        self.turno.refresh_from_db()
        self.assertFalse(self.turno.esta_activo)

    def test_esta_disponible_turno_libre(self):
        self.assertTrue(self.turno.esta_disponible())

    def test_esta_disponible_turno_reservado(self):
        self.turno.bloquear()
        self.assertFalse(self.turno.esta_disponible())

    def test_esta_disponible_turno_inactivo(self):
        self.turno.desactivar()
        self.assertFalse(self.turno.esta_disponible())


class TestBloqueHorario(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico10', password='1234')
        medico       = Medico.objects.create(
            user=user, nombre='García', matricula='M010',
            especialidad=especialidad, estado='aprobado'
        )
        self.bloque  = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0),
            duracion_turno=30, activo=True
        )

    def test_desactivar(self):
        self.bloque.desactivar()
        self.bloque.refresh_from_db()
        self.assertFalse(self.bloque.activo)

    def test_obtener_turnos_disponibles(self):
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,30), hora_fin=time(10,0),
            esta_reservado=True, esta_activo=True
        )
        resultado = self.bloque.obtener_turnos_disponibles()
        self.assertEqual(resultado.count(), 1)

    def test_generar_turnos_crea_turnos(self):
        self.bloque.generar_turnos(semanas=2)
        self.assertEqual(Turno.objects.filter(bloque=self.bloque).count(), 4)

    def test_generar_turnos_no_duplica(self):
        self.bloque.generar_turnos(semanas=2)
        inicial = Turno.objects.filter(bloque=self.bloque).count()
        self.bloque.generar_turnos(semanas=2)
        final = Turno.objects.filter(bloque=self.bloque).count()
        self.assertEqual(inicial, final)

    def test_generar_turnos_respeta_reservados(self):
        otro_bloque = BloqueHorario.objects.create(
            medico=self.bloque.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(9,30),
            duracion_turno=30, activo=False
        )
        fecha = date.today() + timedelta(days=(0 - date.today().weekday()) % 7 + 7)
        Turno.objects.create(
            bloque=otro_bloque, fecha=fecha,
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        self.bloque.generar_turnos(semanas=2)
        existe = Turno.objects.filter(
            bloque=self.bloque, fecha=fecha, hora_inicio=time(9,0)
        ).exists()
        self.assertFalse(existe)

    def test_validar_superposicion_true(self):
        otro = BloqueHorario(
            medico=self.bloque.medico, dia_semana=0,
            hora_inicio=time(9,30), hora_fin=time(10,30), duracion_turno=30
        )
        self.assertTrue(self.bloque.validar_superposicion(otro))

    def test_validar_superposicion_false(self):
        otro = BloqueHorario(
            medico=self.bloque.medico, dia_semana=0,
            hora_inicio=time(10,0), hora_fin=time(11,0), duracion_turno=30
        )
        self.assertFalse(self.bloque.validar_superposicion(otro))

    def test_desactivar_desactiva_turnos(self):
        Turno.objects.create(
            bloque=self.bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        self.bloque.desactivar()
        turno = Turno.objects.first()
        self.assertFalse(turno.esta_activo)

    def test_obtener_bloques_activos(self):
        BloqueHorario.objects.create(
            medico=self.bloque.medico, dia_semana=1,
            hora_inicio=time(10,0), hora_fin=time(11,0), duracion_turno=30, activo=False
        )
        activos = BloqueHorario.obtener_bloques_activos(self.bloque.medico)
        self.assertEqual(activos.count(), 1)
        self.assertEqual(activos.first(), self.bloque)


class TestMedico(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(username='medico11', password='1234')
        self.medico  = Medico.objects.create(
            user=user, nombre='García', matricula='M011',
            especialidad=especialidad, estado='pendiente'
        )

    def test_aprobar(self):
        self.medico.aprobar()
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.estado, 'aprobado')

    def test_rechazar(self):
        self.medico.rechazar()
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.estado, 'rechazado')

    def test_esta_aprobado_true(self):
        self.medico.aprobar()
        self.assertTrue(self.medico.esta_aprobado())

    def test_esta_aprobado_false(self):
        self.assertFalse(self.medico.esta_aprobado())

    def test_existe_por_matricula_true(self):
        self.assertTrue(Medico.existe_por_matricula('M011'))

    def test_existe_por_matricula_false(self):
        self.assertFalse(Medico.existe_por_matricula('ZZZZ'))


class TestReserva(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user_med     = User.objects.create_user(username='medico12', password='1234')
        medico       = Medico.objects.create(
            user=user_med, nombre='García', matricula='M012',
            especialidad=especialidad, estado='aprobado'
        )
        bloque       = BloqueHorario.objects.create(
            medico=medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        self.turno   = Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=2),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        user_pac     = User.objects.create_user(username='paciente5', password='1234')
        paciente     = Paciente.objects.create(
            user=user_pac, nombre='Juan', apellido='Lopez', dni='55555555'
        )
        self.reserva = Reserva.objects.create(
            turno=self.turno, paciente=paciente, estado='activa'
        )

    # --- Métodos de cancelar ---
    def test_cancelar(self):
        self.reserva.cancelar()
        self.reserva.refresh_from_db()
        self.turno.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'cancelada')
        self.assertFalse(self.turno.esta_reservado)

    # --- horas_hasta_el_turno ---
    def test_horas_hasta_el_turno(self):
        resultado = self.reserva.horas_hasta_el_turno()
        self.assertGreater(resultado, 0)

    def test_horas_hasta_el_turno_pasado_devuelve_cero_o_negativo(self):
        pasado = timezone.now() - timedelta(days=2)
        self.turno.fecha = pasado.date()
        self.turno.hora_inicio = pasado.time()
        self.turno.save()
        self.reserva.refresh_from_db()
        resultado = self.reserva.horas_hasta_el_turno()
        self.assertLessEqual(resultado, 0)

    # --- Código de reserva ---
    def test_codigo_reserva_generado(self):
        self.assertTrue(self.reserva.codigo_reserva.startswith('RES-'))

    def test_codigo_reserva_unico(self):
        user_pac2 = User.objects.create_user(username='paciente6', password='1234')
        paciente2 = Paciente.objects.create(
            user=user_pac2, nombre='Ana', apellido='Gomez', dni='66666666'
        )
        turno2 = Turno.objects.create(
            bloque=self.turno.bloque,
            fecha=date.today() + timedelta(days=3),
            hora_inicio=time(9,30), hora_fin=time(10,0),
            esta_reservado=True, esta_activo=True
        )
        reserva2 = Reserva.objects.create(turno=turno2, paciente=paciente2)
        self.assertNotEqual(self.reserva.codigo_reserva, reserva2.codigo_reserva)

    # --- es_cancelable ---
    def test_es_cancelable_true(self):
        self.assertTrue(self.reserva.es_cancelable())

    def test_es_cancelable_false_menos_24h(self):
        ahora = timezone.now() + timedelta(hours=12)
        self.turno.fecha = ahora.date()
        self.turno.hora_inicio = ahora.time()
        self.turno.save()
        self.reserva.refresh_from_db()
        self.assertFalse(self.reserva.es_cancelable())

    def test_es_cancelable_false_no_activa(self):
        self.reserva.estado = 'cancelada'
        self.reserva.save()
        self.assertFalse(self.reserva.es_cancelable())

    # --- confirmar_atencion ---
    def test_confirmar_atencion_exitosa(self):
        self.reserva.confirmar_atencion(diagnostico='Paracetamol')
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, 'atendida')
        self.assertEqual(self.reserva.diagnostico, 'Paracetamol')

    def test_confirmar_atencion_no_activa_lanza_error(self):
        self.reserva.estado = 'cancelada'
        self.reserva.save()
        with self.assertRaises(ValidationError):
            self.reserva.confirmar_atencion('test')