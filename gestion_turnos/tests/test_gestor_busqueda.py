from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Especialidad, ObraSocial, Turno, BloqueHorario
)
from gestion_turnos.servicios.gestor_busqueda import GestorBusqueda

class TestGestorBusqueda(TestCase):

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Cardiología')
        self.obra_social  = ObraSocial.objects.create(nombre='OSDE')
        user              = User.objects.create_user(username='medico6', password='1234')
        self.medico       = Medico.objects.create(
            user=user, nombre='García', matricula='M006',
            especialidad=self.especialidad, estado='aprobado'
        )
        self.medico.obras_sociales.add(self.obra_social)
        self.gestor = GestorBusqueda()

    def test_buscar_por_especialidad(self):
        """Buscar por especialidad devuelve médicos correctos."""
        resultado = self.gestor.buscar_medicos(especialidad='Cardiología')
        self.assertIn(self.medico, resultado)

    def test_buscar_especialidad_inexistente_devuelve_vacio(self):
        """Buscar especialidad que no existe devuelve lista vacía."""
        resultado = self.gestor.buscar_medicos(especialidad='Odontología')
        self.assertEqual(resultado.count(), 0)

    def test_buscar_por_obra_social(self):
        """Buscar por obra social devuelve médicos que la aceptan."""
        resultado = self.gestor.buscar_medicos(obra_social='OSDE')
        self.assertIn(self.medico, resultado)

    def test_buscar_obra_social_no_aceptada_devuelve_vacio(self):
        """Médico que no acepta la obra social no aparece."""
        resultado = self.gestor.buscar_medicos(obra_social='PAMI')
        self.assertEqual(resultado.count(), 0)

    def test_buscar_medico_no_aprobado_no_aparece(self):
        """Médico en estado pendiente no aparece en resultados."""
        self.medico.estado = 'pendiente'
        self.medico.save()
        resultado = self.gestor.buscar_medicos(especialidad='Cardiología')
        self.assertNotIn(self.medico, resultado)

    def test_obtener_turnos_disponibles_agrupa_por_fecha(self):
        """obtener_turnos_disponibles devuelve dict agrupado por fecha."""
        bloque = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        resultado = self.gestor.obtener_turnos_disponibles(self.medico.id)
        self.assertIsInstance(resultado, dict)
        self.assertTrue(len(resultado) > 0)

    def test_obtener_turnos_no_incluye_reservados(self):
        """obtener_turnos_disponibles no incluye turnos reservados."""
        bloque = BloqueHorario.objects.create(
            medico=self.medico, dia_semana=0,
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30
        )
        Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=7),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        resultado = self.gestor.obtener_turnos_disponibles(self.medico.id)
        self.assertEqual(len(resultado), 0)