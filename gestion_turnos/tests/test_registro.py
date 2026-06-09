from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from gestion_turnos.models import Medico, Paciente, Especialidad, ObraSocial
from gestion_turnos.servicios.registro import Registro
from gestion_turnos.forms import RegistroMedicoForm, RegistroPacienteForm
from gestion_turnos.models import Provincia, Ciudad, Clinica

class TestRegistroValidarUnicidad(TestCase):

    def setUp(self):
        especialidad = Especialidad.objects.create(nombre='Cardiología')
        user         = User.objects.create_user(
            username='existente', password='1234', email='existe@test.com'
        )
        Paciente.objects.create(
            user=user, nombre='Juan', apellido='Lopez', dni='99999999'
        )
        Medico.objects.create(
            user=user, nombre='García', matricula='MAT999',
            especialidad=especialidad, estado='aprobado'
        )

    def test_email_duplicado_lanza_error(self):
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(email='existe@test.com')

    def test_dni_duplicado_lanza_error(self):
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(dni='99999999')

    def test_matricula_duplicada_lanza_error(self):
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(matricula='MAT999')

    def test_datos_nuevos_no_lanzan_error(self):
        try:
            Registro.validar_unicidad(
                email='nuevo@test.com', dni='00000000', matricula='MAT000'
            )
        except ValidationError:
            self.fail('validar_unicidad lanzó error con datos únicos.')


class TestRegistroRegistrarMedico(TestCase):

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Cardiología')

        # Crear datos para clínica (opción 1)
        provincia = Provincia.objects.create(nombre='Buenos Aires')
        self.ciudad = Ciudad.objects.create(nombre='La Plata', provincia=provincia)
        self.clinica = Clinica.objects.create(
            nombre='Hospital Italiano',
            calle='Av. Belgrano', numero='1500',
            ciudad=self.ciudad
        )

        # Datos base del formulario (sin decidir aún clínica o particular)
        self.datos_base = {
            'username':   'dr_garcia',
            'password1':  'Password1234!',
            'password2':  'Password1234!',
            'nombre':     'Martín',
            'apellido':   'García',
            'especialidad': self.especialidad.id,
            'matricula':  'M100',
        }

    def test_registrar_medico_con_clinica_crea_user(self):
        """Registro exitoso seleccionando una clínica."""
        datos = self.datos_base.copy()
        datos['clinica'] = self.clinica.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad, clinica=self.clinica
        )
        self.assertTrue(User.objects.filter(username='dr_garcia').exists())

    def test_registrar_medico_con_clinica_crea_perfil(self):
        datos = self.datos_base.copy()
        datos['clinica'] = self.clinica.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad, clinica=self.clinica
        )
        self.assertTrue(Medico.objects.filter(matricula='M100').exists())

    def test_registrar_medico_con_particular_crea_user(self):
        """Registro exitoso marcando 'atiende de forma particular' y completando datos."""
        datos = self.datos_base.copy()
        datos['es_particular'] = True
        datos['calle'] = 'Calle Falsa'
        datos['numero'] = '123'
        datos['piso_depto'] = '1B'
        datos['telefono_consultorio'] = '3794000000'
        datos['ciudad_consultorio'] = self.ciudad.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario,
            matricula='M100',
            especialidad=self.especialidad,
            es_particular=True,
            calle='Calle Falsa',
            numero='123',
            piso_depto='1B',
            telefono_consultorio='3794000000',
            ciudad_consultorio=self.ciudad,
        )
        self.assertTrue(User.objects.filter(username='dr_garcia').exists())

    def test_registrar_medico_con_particular_crea_perfil(self):
        datos = self.datos_base.copy()
        datos['es_particular'] = True
        datos['calle'] = 'Calle Falsa'
        datos['numero'] = '123'
        datos['piso_depto'] = '1B'
        datos['telefono_consultorio'] = '3794000000'
        datos['ciudad_consultorio'] = self.ciudad.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario,
            matricula='M100',
            especialidad=self.especialidad,
            es_particular=True,
            calle='Calle Falsa',
            numero='123',
            piso_depto='1B',
            telefono_consultorio='3794000000',
            ciudad_consultorio=self.ciudad,
        )
        self.assertTrue(Medico.objects.filter(matricula='M100').exists())

    def test_registrar_medico_estado_pendiente_con_clinica(self):
        """Médico registrado con clínica queda en estado pendiente."""
        datos = self.datos_base.copy()
        datos['clinica'] = self.clinica.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        medico  = Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad, clinica=self.clinica
        )
        self.assertEqual(medico.estado, 'pendiente')

    def test_registrar_medico_estado_pendiente_con_particular(self):
        """Médico registrado como particular queda en estado pendiente."""
        datos = self.datos_base.copy()
        datos['es_particular'] = True
        datos['calle'] = 'Calle Falsa'
        datos['numero'] = '123'
        datos['ciudad_consultorio'] = self.ciudad.id
        form = RegistroMedicoForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        medico  = Registro.registrar_medico(
            usuario=usuario,
            matricula='M100',
            especialidad=self.especialidad,
            es_particular=True,
            calle='Calle Falsa',
            numero='123',
            ciudad_consultorio=self.ciudad,
        )
        self.assertEqual(medico.estado, 'pendiente')

class TestRegistroRegistrarPaciente(TestCase):

    def setUp(self):
        self.datos = {
            'username':  'juan_lopez',
            'password1': 'Password1234!',
            'password2': 'Password1234!',
            'nombre':    'Juan',
            'apellido':  'Lopez',
            'dni':       '44444444',
            'telefono':  '3794000000',
        }

    def test_registrar_paciente_crea_user(self):
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertTrue(User.objects.filter(username='juan_lopez').exists())

    def test_registrar_paciente_crea_perfil(self):
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertTrue(Paciente.objects.filter(dni='44444444').exists())

    def test_registrar_paciente_dni_correcto(self):
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario  = Registro.registrar_usuario(form)
        paciente = Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertEqual(paciente.dni, '44444444')


class TestRegistroFortalezaContrasena(TestCase):

    def test_contrasena_corta_lanza_error(self):
        with self.assertRaises(ValidationError):
            Registro.validar_fortaleza_contrasena('1234')

    def test_contrasena_larga_no_lanza_error(self):
        try:
            Registro.validar_fortaleza_contrasena('12345678')
        except ValidationError:
            self.fail('validar_fortaleza_contrasena lanzó error con contraseña válida.')