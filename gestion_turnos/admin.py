from django.contrib import admin

from .models import BloqueHorario, Medico, Paciente, Turno

admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(BloqueHorario)
admin.site.register(Turno)