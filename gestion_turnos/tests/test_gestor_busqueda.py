from django.test import TestCase
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Medico, Especialidad, ObraSocial, Turno, BloqueHorario, Clinica, Ciudad, Provincia,
)
from gestion_turnos.servicios.gestor_busqueda import GestorBusqueda

class TestGestorBusqueda(TestCase):

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Cardiología')
        self.obra_social  = ObraSocial.objects.create(nombre='OSDE')

        # Médico aprobado con nombre de usuario completo
        user_aprobado = User.objects.create_user(
            username='medico_aprobado', password='1234',
            first_name='Juan', last_name='García'          # ← importante
        )
        self.medico_aprobado = Medico.objects.create(
            user=user_aprobado, nombre='Juan García', matricula='M001',
            especialidad=self.especialidad, estado='aprobado'
        )
        self.medico_aprobado.obras_sociales.add(self.obra_social)

        # Médico pendiente
        user_pendiente = User.objects.create_user(
            username='medico_pendiente', password='1234',
            first_name='Pedro', last_name='Pérez'
        )
        self.medico_pendiente = Medico.objects.create(
            user=user_pendiente, nombre='Pedro Pérez', matricula='M002',
            especialidad=self.especialidad, estado='pendiente'
        )

    # ------------------------------------------------------------
    # buscar_medicos
    # ------------------------------------------------------------
    def test_buscar_por_especialidad(self):
        resultado = GestorBusqueda.buscar_medicos(especialidad='Cardiología')
        self.assertIn(self.medico_aprobado, resultado)

    def test_buscar_especialidad_inexistente_devuelve_vacio(self):
        resultado = GestorBusqueda.buscar_medicos(especialidad='Odontología')
        self.assertFalse(resultado.exists())

    def test_buscar_por_nombre_de_usuario(self):
        # Busca por el apellido del usuario vinculado
        resultado = GestorBusqueda.buscar_medicos(nombre='García')
        self.assertIn(self.medico_aprobado, resultado)

    def test_buscar_por_nombre_de_usuario_parcial(self):
        # Busca por una parte del nombre de pila
        resultado = GestorBusqueda.buscar_medicos(nombre='Juan')
        self.assertIn(self.medico_aprobado, resultado)

    def test_buscar_por_nombre_inexistente_devuelve_vacio(self):
        resultado = GestorBusqueda.buscar_medicos(nombre='Nadie')
        self.assertFalse(resultado.exists())

    def test_buscar_por_obra_social(self):
        resultado = GestorBusqueda.buscar_medicos(obra_social='OSDE')
        self.assertIn(self.medico_aprobado, resultado)

    def test_buscar_obra_social_no_aceptada_devuelve_vacio(self):
        resultado = GestorBusqueda.buscar_medicos(obra_social='PAMI')
        self.assertFalse(resultado.exists())

    def test_buscar_medico_no_aprobado_no_aparece(self):
        resultado = GestorBusqueda.buscar_medicos(especialidad='Cardiología')
        self.assertNotIn(self.medico_pendiente, resultado)

    def test_buscar_por_ciudad_en_clinica(self):
        provincia = Provincia.objects.create(nombre='Buenos Aires')
        ciudad    = Ciudad.objects.create(nombre='La Plata', provincia=provincia)
        clinica   = Clinica.objects.create(
            nombre='Hospital', calle='1', numero='1', ciudad=ciudad
        )
        user = User.objects.create_user(username='medico_clinica', password='1234')
        medico = Medico.objects.create(
            user=user, nombre='Medico Clinica', matricula='M003',
            especialidad=self.especialidad, estado='aprobado', clinica=clinica
        )
        resultado = GestorBusqueda.buscar_medicos(ciudad='La Plata')
        self.assertIn(medico, resultado)

    def test_buscar_por_ciudad_en_consultorio_particular(self):
        provincia = Provincia.objects.create(nombre='Córdoba')
        ciudad    = Ciudad.objects.create(nombre='Córdoba Capital', provincia=provincia)
        user = User.objects.create_user(username='medico_particular', password='1234')
        medico = Medico.objects.create(
            user=user, nombre='Medico Particular', matricula='M004',
            especialidad=self.especialidad, estado='aprobado', es_particular=True
        )
        from gestion_turnos.models import ConsultorioParticular
        ConsultorioParticular.objects.create(
            medico=medico, calle='Calle', numero='123', ciudad=ciudad
        )
        resultado = GestorBusqueda.buscar_medicos(ciudad='Córdoba Capital')
        self.assertIn(medico, resultado)

    # ------------------------------------------------------------
    # obtener_perfil_medico
    # ------------------------------------------------------------
    def test_obtener_perfil_medico_devuelve_aprobado(self):
        medico = GestorBusqueda.obtener_perfil_medico(self.medico_aprobado.id)
        self.assertEqual(medico, self.medico_aprobado)

    def test_obtener_perfil_medico_rechaza_no_aprobado(self):
        from django.http import Http404
        with self.assertRaises(Http404):
            GestorBusqueda.obtener_perfil_medico(self.medico_pendiente.id)

    # ------------------------------------------------------------
    # obtener_turnos_disponibles
    # ------------------------------------------------------------
    def test_obtener_turnos_disponibles_agrupa_por_fecha(self):
        bloque = BloqueHorario.objects.create(
            medico=self.medico_aprobado, dia_semana=date.today().weekday(),
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=False, esta_activo=True
        )
        resultado = GestorBusqueda.obtener_turnos_disponibles(self.medico_aprobado.id)
        self.assertIsInstance(resultado, dict)
        self.assertTrue(len(resultado) > 0)

    def test_obtener_turnos_no_incluye_reservados(self):
        bloque = BloqueHorario.objects.create(
            medico=self.medico_aprobado, dia_semana=date.today().weekday(),
            hora_inicio=time(9,0), hora_fin=time(10,0), duracion_turno=30, activo=True
        )
        Turno.objects.create(
            bloque=bloque,
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(9,0), hora_fin=time(9,30),
            esta_reservado=True, esta_activo=True
        )
        resultado = GestorBusqueda.obtener_turnos_disponibles(self.medico_aprobado.id)
        self.assertEqual(len(resultado), 0)

    def test_obtener_turnos_no_incluye_pasados(self):
        hoy = date.today()
        # Creamos turno para hoy en hora pasada (inviable reservarlo)
        bloque = BloqueHorario.objects.create(
            medico=self.medico_aprobado, dia_semana=hoy.weekday(),
            hora_inicio=time(0,0), hora_fin=time(1,0), duracion_turno=60, activo=True
        )
        Turno.objects.create(
            bloque=bloque,
            fecha=hoy,
            hora_inicio=time(0,0), hora_fin=time(1,0),
            esta_reservado=False, esta_activo=True
        )
        resultado = GestorBusqueda.obtener_turnos_disponibles(self.medico_aprobado.id)
        # La fecha de inicio por defecto es hoy, pero el turno ya empezó a las 00:00.
        # Para este test, lo importante es que no aparezca si forzamos rango desde hoy.
        # Podemos ajustar: el método excluye hora_inicio < ahora, así que no debería aparecer.
        self.assertEqual(len(resultado), 0)

    # ------------------------------------------------------------
    # obtener_siguiente_semana / obtener_semana_anterior
    # ------------------------------------------------------------
    def test_obtener_siguiente_semana(self):
        fecha = date.today()
        siguiente = GestorBusqueda.obtener_siguiente_semana(fecha)
        self.assertEqual(siguiente, fecha + timedelta(weeks=1))

    def test_obtener_semana_anterior(self):
        fecha = date.today()
        anterior = GestorBusqueda.obtener_semana_anterior(fecha)
        self.assertEqual(anterior, fecha - timedelta(weeks=1))