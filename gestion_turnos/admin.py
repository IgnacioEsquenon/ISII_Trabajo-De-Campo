from django.contrib import admin

from .models import Medico, Paciente, Especialidad, ObraSocial, Reserva, Provincia, Clinica, Ciudad, ConsultorioParticular

admin.site.register(Medico)
admin.site.register(Paciente)
admin.site.register(Especialidad)
admin.site.register(ObraSocial)
admin.site.register(Reserva)
admin.site.register(Provincia)
admin.site.register(Clinica)
admin.site.register(Ciudad)
admin.site.register(ConsultorioParticular)