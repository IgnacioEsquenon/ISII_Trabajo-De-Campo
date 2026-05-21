from django.contrib import admin

from .models import Medico, Paciente, Especialidad, ObraSocial

admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(Especialidad)
admin.site.register(ObraSocial)
