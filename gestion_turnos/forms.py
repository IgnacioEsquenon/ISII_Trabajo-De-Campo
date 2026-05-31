from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from gestion_turnos.models.ciudad import Ciudad
from .models import BloqueHorario, Medico, Paciente, Especialidad, ObraSocial
from gestion_turnos.models.clinica import Clinica

class RegistroMedicoForm(UserCreationForm):
    nombre       = forms.CharField(max_length=100)
    apellido     = forms.CharField(max_length=100)
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all())
    matricula    = forms.CharField(max_length=50)
    obras_sociales = forms.ModelMultipleChoiceField(
        queryset = ObraSocial.objects.all(),
        widget   = forms.CheckboxSelectMultiple,
        required = False
    )
    clinica = forms.ModelChoiceField(
        queryset    = Clinica.objects.all(),
        required    = False,
        label       = 'Clínica donde atiende',
        empty_label = 'Seleccioná una clínica'
    )
    es_particular        = forms.BooleanField(required=False)   # ← agregado
    calle                = forms.CharField(max_length=100, required=False)  # ← agregado
    numero               = forms.CharField(max_length=20,  required=False)  # ← agregado
    piso_depto           = forms.CharField(max_length=30,  required=False)  # ← agregado
    telefono_consultorio = forms.CharField(max_length=25,  required=False)  # ← agregado
    ciudad_consultorio = forms.ModelChoiceField(
    queryset    = Ciudad.objects.all(),
    required    = False,
    label       = 'Ciudad del consultorio',
    empty_label = 'Seleccioná una ciudad'
)

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido')

    def clean(self):
        cleaned       = super().clean()
        clinica       = cleaned.get('clinica')
        es_particular = cleaned.get('es_particular')
        calle         = cleaned.get('calle')

        if not clinica and not es_particular:
            raise forms.ValidationError(
                'Debe seleccionar una clínica o indicar que atiende de forma particular.'
            )
        if es_particular and not calle:
            raise forms.ValidationError(
                'Si atiende de forma particular debe ingresar la dirección del consultorio.'
            )
        return cleaned

    # save() eliminado — la lógica está en Registro.registrar_medico()


class RegistroPacienteForm(UserCreationForm):
    nombre      = forms.CharField(max_length=100)
    apellido    = forms.CharField(max_length=100)
    dni         = forms.CharField(max_length=20)
    telefono    = forms.CharField(max_length=20, required=False)
    obra_social = forms.ModelChoiceField(
        queryset    = ObraSocial.objects.all(),
        required    = False,
        label       = 'Obra social',
        empty_label = 'Sin obra social'
    )

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido')

    # save() eliminado — la lógica está en Registro.registrar_paciente()


class BloqueHorarioForm(forms.ModelForm):
    class Meta:
        model  = BloqueHorario
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'duracion_turno']
        widgets = {
            'hora_inicio':    forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'hora_fin':       forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'duracion_turno': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        inicio  = cleaned.get('hora_inicio')
        fin     = cleaned.get('hora_fin')
        if inicio and fin and fin <= inicio:
            raise forms.ValidationError("La hora de fin debe ser posterior al inicio.")
        return cleaned