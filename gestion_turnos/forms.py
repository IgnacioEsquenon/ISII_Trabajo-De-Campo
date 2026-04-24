from django import forms
from .models import BloqueHorario  
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Medico, Paciente

class RegistroMedicoForm(UserCreationForm):
    # Heredamos usuario y contraseñas automáticamente de UserCreationForm
    nombre = forms.CharField(max_length=100, required=True)
    apellido = forms.CharField(max_length=100, required=True)
    especialidad = forms.CharField(max_length=100, required=True)
    matricula = forms.CharField(max_length=50, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # Le decimos a Django qué campos mostrar arriba de todo
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido')

    def save(self, commit=True):
        # 1. Guardamos el User de Django (encripta la contraseña automáticamente)
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre']
        user.last_name = self.cleaned_data['apellido']
        
        if commit:
            user.save() # Se guarda en la tabla auth_user
            
            nombre_completo = f"{self.cleaned_data['nombre']} {self.cleaned_data['apellido']}"

            # 2. Creamos el perfil de Médico y lo vinculamos a ese User
            Medico.objects.create(
                user=user,
                nombre=nombre_completo,
                especialidad=self.cleaned_data['especialidad'],
                matricula=self.cleaned_data['matricula']
            )
        return user
    
class RegistroPacienteForm(UserCreationForm):
    nombre = forms.CharField(max_length=100, required=True)
    apellido = forms.CharField(max_length=100, required=True)
    dni = forms.CharField(max_length=20, required=True)
    telefono = forms.CharField(max_length=20, required=False) 

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nombre', 'apellido')

    def save(self, commit=True):
        # 1. Guardamos el User base (con su contraseña encriptada)
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre']
        user.last_name = self.cleaned_data['apellido']
        
        if commit:
            user.save()
            
            # 2. Creamos el perfil de Paciente vinculado
            Paciente.objects.create(
                user=user,
                nombre=self.cleaned_data['nombre'],    
                apellido=self.cleaned_data['apellido'],
                dni=self.cleaned_data['dni'],
                telefono=self.cleaned_data['telefono']
            )
        return user

class BloqueHorarioForm(forms.ModelForm):
    class Meta:
        model = BloqueHorario
        fields = ['dia_semana', 'hora_inicio', 'hora_fin','duracion_turno' ] 
        widgets = {
            'hora_inicio': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'duracion_turno': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('hora_inicio')
        fin    = cleaned.get('hora_fin')
        if inicio and fin and fin <= inicio:
            raise forms.ValidationError("La hora de fin debe ser posterior al inicio.")
        return cleaned