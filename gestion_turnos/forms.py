from django import forms
from .models import BloqueHorario 

class BloqueHorarioForm(forms.ModelForm):
    class Meta:
        model = BloqueHorario
        fields = ['dia_semana', 'hora_inicio', 'hora_fin','duracion_turno' ,'activo']
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