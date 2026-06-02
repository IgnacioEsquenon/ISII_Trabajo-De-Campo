from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from gestion_turnos.models import Medico, Paciente, Especialidad, ObraSocial
from gestion_turnos.servicios.registro import Registro
from gestion_turnos.forms import RegistroMedicoForm, RegistroPacienteForm


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
        """Email ya registrado lanza ValidationError."""
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(email='existe@test.com')

    def test_dni_duplicado_lanza_error(self):
        """DNI ya registrado lanza ValidationError."""
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(dni='99999999')

    def test_matricula_duplicada_lanza_error(self):
        """Matrícula ya registrada lanza ValidationError."""
        with self.assertRaises(ValidationError):
            Registro.validar_unicidad(matricula='MAT999')

    def test_datos_nuevos_no_lanzan_error(self):
        """Datos únicos no lanzan ningún error."""
        try:
            Registro.validar_unicidad(
                email='nuevo@test.com', dni='00000000', matricula='MAT000'
            )
        except ValidationError:
            self.fail('validar_unicidad lanzó error con datos únicos.')


class TestRegistroRegistrarMedico(TestCase):

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre='Cardiología')
        self.datos = {
            'username':   'dr_garcia',
            'password1':  'Password1234!',
            'password2':  'Password1234!',
            'nombre':     'Martín',
            'apellido':   'García',
            'especialidad': self.especialidad.id,
            'matricula':  'M100',
        }

    def test_registrar_medico_crea_user(self):
        """Registrar médico crea el User de Django."""
        form = RegistroMedicoForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad
        )
        self.assertTrue(User.objects.filter(username='dr_garcia').exists())

    def test_registrar_medico_crea_perfil(self):
        """Registrar médico crea el perfil Medico vinculado."""
        form = RegistroMedicoForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad
        )
        self.assertTrue(Medico.objects.filter(matricula='M100').exists())

    def test_registrar_medico_estado_aprobado(self):
        """Médico registrado queda en estado aprobado por defecto."""
        form = RegistroMedicoForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        medico  = Registro.registrar_medico(
            usuario=usuario, matricula='M100',
            especialidad=self.especialidad
        )
        self.assertEqual(medico.estado, 'aprobado')


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
        """Registrar paciente crea el User de Django."""
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertTrue(User.objects.filter(username='juan_lopez').exists())

    def test_registrar_paciente_crea_perfil(self):
        """Registrar paciente crea el perfil Paciente vinculado."""
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario = Registro.registrar_usuario(form)
        Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertTrue(Paciente.objects.filter(dni='44444444').exists())

    def test_registrar_paciente_dni_correcto(self):
        """El DNI del paciente se guarda correctamente."""
        form = RegistroPacienteForm(self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        usuario  = Registro.registrar_usuario(form)
        paciente = Registro.registrar_paciente(
            usuario=usuario, dni='44444444', telefono='3794000000'
        )
        self.assertEqual(paciente.dni, '44444444') 

