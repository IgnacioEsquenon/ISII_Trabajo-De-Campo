from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from gestion_turnos.models import Medico, Paciente

class Registro:
    """
    Fachada de registro. Centraliza la creación de usuarios,
    médicos y pacientes validando unicidad antes de persistir.
    """

    @staticmethod
    def validar_unicidad(email=None, dni=None, matricula=None):
        """
        Valida que no existan duplicados de email, dni o matrícula
        antes de crear cualquier usuario.
        """
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(f"Ya existe un usuario con el email {email}.")

        if dni and Paciente.objects.filter(dni=dni).exists():
            raise ValidationError(f"Ya existe un paciente con el DNI {dni}.")

        if matricula and Medico.objects.filter(matricula=matricula).exists():
            raise ValidationError(f"Ya existe un médico con la matrícula {matricula}.")

    @staticmethod
    def registrar_usuario(form):
        """
        Crea el User base de Django a partir del formulario.
        Devuelve el User creado sin guardarlo aún (commit=False).
        """
        user            = form.save(commit=False)
        user.first_name = form.cleaned_data['nombre']
        user.last_name  = form.cleaned_data['apellido']
        return user

    @staticmethod
    def registrar_paciente(usuario, dni, telefono, obra_social=None):
        """Crea el perfil Paciente vinculado al usuario."""
        from gestion_turnos.models import Paciente
        usuario.save()
        return Paciente.objects.create(
            user        = usuario,
            nombre      = usuario.first_name,
            apellido    = usuario.last_name,
            dni         = dni,  
            telefono    = telefono,
            obra_social = obra_social,
        )
    
    @staticmethod
    def registrar_medico(usuario, matricula, especialidad, estado='pendiente', clinica=None, obras_sociales=None):
        """
        Crea el perfil Medico vinculado al usuario.
        El médico queda en estado 'pendiente' hasta que el admin lo apruebe.
        """
        usuario.save()
        es_particular = clinica is None

        medico = Medico.objects.create(
            user          = usuario,
            nombre        = f"{usuario.first_name} {usuario.last_name}",
            matricula     = matricula,
            especialidad  = especialidad,
            estado        = estado,
            clinica       = clinica,
            es_particular = es_particular,
        )

        if obras_sociales:
            medico.obras_sociales.set(obras_sociales)

        return medico