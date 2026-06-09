from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from gestion_turnos.models import Medico, Paciente, Clinica, Provincia, Ciudad, ConsultorioParticular


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
    def validar_fortaleza_contrasena(contrasena):
        if len(contrasena) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

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
    def registrar_medico(usuario, matricula, especialidad, estado='pendiente', clinica=None, obras_sociales=None, **kwargs):
        """
        Crea el perfil Medico vinculado al usuario.
        Si es particular también crea el ConsultorioParticular.
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

    # Si atiende de forma particular creamos su consultorio
        if es_particular and kwargs.get('calle'):
            ConsultorioParticular.objects.create(
                medico     = medico,
                calle      = kwargs.get('calle', ''),
                numero     = kwargs.get('numero', ''),
                piso_depto = kwargs.get('piso_depto', ''),
                telefono   = kwargs.get('telefono_consultorio', ''),
                ciudad     = kwargs.get('ciudad_consultorio'),  
            )

        return medico