# ============================================================
# MEDORA — Script de carga de datos de prueba (autocontenido)
# Region: Corrientes / Chaco, Argentina
# Ejecutar: python manage.py shell < gestion_turnos/fixtures/cargar_datos_prueba.py
# ============================================================

from datetime import date, time, timedelta, datetime
from django.contrib.auth.models import User
from gestion_turnos.models import (
    Provincia, Ciudad, Clinica, Especialidad, ObraSocial,
    Medico, Paciente, ConsultorioParticular,
    BloqueHorario, Turno, Reserva
)

# ── Limpiar datos anteriores ────────────────────────────────────
User.objects.filter(username__startswith="med_").delete()
User.objects.filter(username__startswith="pac_").delete()

# ── Provincias ─────────────────────────────────────────────────
p_corrientes, _ = Provincia.objects.get_or_create(nombre="Corrientes")
p_chaco, _      = Provincia.objects.get_or_create(nombre="Chaco")

# ── Ciudades ───────────────────────────────────────────────────
c_corrientes,   _ = Ciudad.objects.get_or_create(nombre="Corrientes", provincia=p_corrientes)
c_resistencia,  _ = Ciudad.objects.get_or_create(nombre="Resistencia", provincia=p_chaco)
c_goya,         _ = Ciudad.objects.get_or_create(nombre="Goya", provincia=p_corrientes)
c_paso_libres,  _ = Ciudad.objects.get_or_create(nombre="Paso de los Libres", provincia=p_corrientes)
c_curuzu,       _ = Ciudad.objects.get_or_create(nombre="Curuzu Cuatia", provincia=p_corrientes)
c_mercedes,     _ = Ciudad.objects.get_or_create(nombre="Mercedes", provincia=p_corrientes)

# ── Especialidades ─────────────────────────────────────────────
esp_cardio,   _ = Especialidad.objects.get_or_create(nombre="Cardiologia", defaults={"descripcion": "Enfermedades del corazon"})
esp_derma,    _ = Especialidad.objects.get_or_create(nombre="Dermatologia", defaults={"descripcion": "Enfermedades de la piel"})
esp_pediatria,_ = Especialidad.objects.get_or_create(nombre="Pediatria", defaults={"descripcion": "Salud infantil"})
esp_clinica,  _ = Especialidad.objects.get_or_create(nombre="Clinica Medica", defaults={"descripcion": "Atencion general"})
esp_gineco,   _ = Especialidad.objects.get_or_create(nombre="Ginecologia", defaults={"descripcion": "Salud femenina"})
esp_oftalmo,  _ = Especialidad.objects.get_or_create(nombre="Oftalmologia", defaults={"descripcion": "Enfermedades oculares"})
esp_neuro,    _ = Especialidad.objects.get_or_create(nombre="Neurologia", defaults={"descripcion": "Sistema nervioso"})
esp_trauma,   _ = Especialidad.objects.get_or_create(nombre="Traumatologia", defaults={"descripcion": "Lesiones oseas"})

# ── Obras Sociales ─────────────────────────────────────────────
os_ioscor, _ = ObraSocial.objects.get_or_create(nombre="IOSCOR", defaults={"siglas": "IOSCOR"})
os_pami,   _ = ObraSocial.objects.get_or_create(nombre="PAMI", defaults={"siglas": "PAMI"})
os_osde,   _ = ObraSocial.objects.get_or_create(nombre="OSDE", defaults={"siglas": "OSDE"})
os_swiss,  _ = ObraSocial.objects.get_or_create(nombre="Swiss Medical", defaults={"siglas": "SM"})
os_galeno, _ = ObraSocial.objects.get_or_create(nombre="Galeno", defaults={"siglas": "GAL"})
os_osplad, _ = ObraSocial.objects.get_or_create(nombre="OSPLAD", defaults={"siglas": "OSPLAD"})

# ── Clinicas ────────────────────────────────────────────────────
clinica_corrientes, _ = Clinica.objects.get_or_create(
    nombre="Sanatorio Corrientes",
    defaults={"calle": "Av. 3 de Abril", "numero": "1048", "telefono": "379-4422000", "ciudad": c_corrientes}
)
clinica_resistencia, _ = Clinica.objects.get_or_create(
    nombre="Hospital Escuela Jose de San Martin",
    defaults={"calle": "Av. Las Heras", "numero": "350", "telefono": "362-4441000", "ciudad": c_resistencia}
)
clinica_goya, _ = Clinica.objects.get_or_create(
    nombre="Clinica Goya",
    defaults={"calle": "Av. Sarmiento", "numero": "780", "telefono": "3777-430000", "ciudad": c_goya}
)

# ── Medicos ─────────────────────────────────────────────────────
def crear_medico(username, nombre, apellido, matricula, especialidad, clinica=None, es_particular=False, obras_sociales=None, ciudad_consultorio=None):
    user = User.objects.create_user(username=username, password="med1234", first_name=nombre, last_name=apellido)
    medico = Medico.objects.create(
        user=user, nombre=f"{nombre} {apellido}",
        matricula=matricula, especialidad=especialidad,
        estado="aprobado", clinica=clinica, es_particular=es_particular
    )
    if obras_sociales:
        medico.obras_sociales.set(obras_sociales)
    if es_particular and ciudad_consultorio:
        ConsultorioParticular.objects.create(medico=medico, calle="Calle Principal", numero="123", ciudad=ciudad_consultorio)
    return medico

med_fernandez = crear_medico("med_fernandez", "Laura", "Fernandez", "M-1001", esp_cardio, clinica_corrientes, False, [os_ioscor, os_osde, os_swiss])
med_gonzalez  = crear_medico("med_gonzalez", "Carlos", "Gonzalez", "M-1002", esp_derma, clinica_corrientes, False, [os_ioscor, os_pami])
med_rodriguez = crear_medico("med_rodriguez", "Maria", "Rodriguez", "M-1003", esp_pediatria, clinica_resistencia, False, [os_osde, os_swiss])
med_martinez  = crear_medico("med_martinez", "Jorge", "Martinez", "M-1004", esp_clinica, clinica_goya, False, [os_pami, os_galeno, os_osplad])
med_garcia    = crear_medico("med_garcia", "Ana", "Garcia", "M-1005", esp_gineco, clinica_corrientes, False, [os_ioscor, os_osde])
med_lopez     = crear_medico("med_lopez", "Pedro", "Lopez", "M-1006", esp_neuro, clinica_resistencia, False, [os_swiss, os_pami])
med_ramirez   = crear_medico("med_ramirez", "Sofia", "Ramirez", "M-1007", esp_oftalmo, es_particular=True, obras_sociales=[os_osde, os_swiss], ciudad_consultorio=c_corrientes)
med_torres    = crear_medico("med_torres", "Daniel", "Torres", "M-1008", esp_trauma, es_particular=True, obras_sociales=[os_ioscor, os_pami, os_galeno], ciudad_consultorio=c_resistencia)
med_diaz      = crear_medico("med_diaz", "Lucia", "Diaz", "M-1009", esp_derma, es_particular=True, obras_sociales=[os_osde, os_galeno], ciudad_consultorio=c_goya)
med_sosa      = crear_medico("med_sosa", "Miguel", "Sosa", "M-1010", esp_clinica, es_particular=True, obras_sociales=[os_ioscor, os_swiss, os_pami], ciudad_consultorio=c_corrientes)

# ── Pacientes ───────────────────────────────────────────────────
def crear_paciente(username, nombre, apellido, dni, obra_social=None):
    user = User.objects.create_user(username=username, password="pac1234", first_name=nombre, last_name=apellido)
    return Paciente.objects.create(user=user, nombre=nombre, apellido=apellido, dni=dni, telefono="379-4000000", obra_social=obra_social)

pac_gomez     = crear_paciente("pac_gomez", "Juan", "Gomez", "20123456", os_ioscor)
pac_lopez     = crear_paciente("pac_lopez", "Maria", "Lopez", "20234567", os_osde)
pac_ramirez   = crear_paciente("pac_ramirez", "Carlos", "Ramirez", "20345678", os_pami)
pac_fernandez = crear_paciente("pac_fernandez", "Ana", "Fernandez", "20456789", os_swiss)
pac_martinez  = crear_paciente("pac_martinez", "Pedro", "Martinez", "20567890", os_galeno)
pac_gonzalez  = crear_paciente("pac_gonzalez", "Sofia", "Gonzalez", "20678901", os_osplad)
pac_diaz      = crear_paciente("pac_diaz", "Daniel", "Diaz", "20789012", os_ioscor)
pac_torres    = crear_paciente("pac_torres", "Lucia", "Torres", "20890123", os_osde)

# ── Bloques Horarios (Lunes a Viernes 8-12 y L/M/X 16-19) ────
hoy = date.today()
def crear_bloque(medico, dia_semana, hora_inicio, hora_fin, duracion):
    return BloqueHorario.objects.create(
        medico=medico, dia_semana=dia_semana,
        hora_inicio=hora_inicio, hora_fin=hora_fin,
        duracion_turno=duracion, activo=True
    )

bloques = []
for medico in [med_fernandez, med_gonzalez, med_rodriguez, med_martinez, med_garcia, med_lopez, med_ramirez, med_torres, med_diaz, med_sosa]:
    for dia in range(0, 5):
        bloques.append(crear_bloque(medico, dia, time(8,0), time(12,0), 30))
    for dia in [0, 2, 4]:
        bloques.append(crear_bloque(medico, dia, time(16,0), time(19,0), 30))

# ── Generar turnos futuros ──────────────────────────────────────
for bloque in bloques:
    bloque.generar_turnos(semanas=4)

# ── Generar turnos PASADOS (hace 2 semanas) para tener donde reservar ──
fecha_pasada_inicio = hoy - timedelta(days=14)
while fecha_pasada_inicio.weekday() >= 5:
    fecha_pasada_inicio -= timedelta(days=1)

for bloque in bloques:
    for dia_offset in range(5):
        fecha = fecha_pasada_inicio + timedelta(days=dia_offset)
        if fecha.weekday() == bloque.dia_semana:
            hora_actual = bloque.hora_inicio
            while hora_actual < bloque.hora_fin:
                hora_fin = (datetime.combine(fecha, hora_actual) + timedelta(minutes=bloque.duracion_turno)).time()
                if not Turno.objects.filter(bloque=bloque, fecha=fecha, hora_inicio=hora_actual).exists():
                    Turno.objects.create(
                        bloque=bloque, fecha=fecha,
                        hora_inicio=hora_actual, hora_fin=hora_fin,
                        esta_reservado=False, esta_activo=True
                    )
                hora_actual = (datetime.combine(fecha, hora_actual) + timedelta(minutes=bloque.duracion_turno)).time()

# ── Funcion auxiliar para crear reservas ────────────────────────
def crear_reserva(paciente, medico, fecha_turno, hora_turno, estado, diagnostico="", motivo=""):
    turno = Turno.objects.filter(
        bloque__medico=medico, fecha=fecha_turno, hora_inicio=hora_turno,
        esta_reservado=False, esta_activo=True
    ).first()
    if turno:
        turno.bloquear()
        return Reserva.objects.create(
            turno=turno, paciente=paciente, estado=estado,
            diagnostico=diagnostico, motivo_consulta=motivo
        )
    else:
        print(f"No se encontro turno para {fecha_turno} {hora_turno} - Medico {medico.nombre}")
        return None

# ── Reservas pasadas (atendidas) ────────────────────────────────
# Lunes
crear_reserva(pac_gomez, med_fernandez, fecha_pasada_inicio, time(8,0), "atendida", "Hipertension controlada. Se ajusta medicacion.", "Control de presion")
crear_reserva(pac_lopez, med_fernandez, fecha_pasada_inicio, time(9,0), "atendida", "Ecocardiograma normal.", "Dolor en el pecho")
# Martes
crear_reserva(pac_gomez, med_fernandez, fecha_pasada_inicio + timedelta(days=1), time(10,0), "atendida", "Control de rutina. Sin novedades.", "Chequeo general")
crear_reserva(pac_ramirez, med_gonzalez, fecha_pasada_inicio + timedelta(days=1), time(8,0), "atendida", "Dermatitis atopica. Se prescribe crema.", "Erupcion en brazos")
# Miercoles
crear_reserva(pac_gomez, med_fernandez, fecha_pasada_inicio + timedelta(days=2), time(11,0), "atendida", "Electrocardiograma con resultado normal.", "Dolor toracico")
crear_reserva(pac_martinez, med_martinez, fecha_pasada_inicio + timedelta(days=2), time(8,0), "atendida", "Sindrome gripal. Reposo y paracetamol.", "Fiebre y tos")
# Jueves
crear_reserva(pac_gomez, med_torres, fecha_pasada_inicio + timedelta(days=3), time(9,0), "atendida", "Esguince de tobillo. Inmovilizacion.", "Dolor en tobillo")
crear_reserva(pac_torres, med_ramirez, fecha_pasada_inicio + timedelta(days=3), time(8,0), "atendida", "Fondo de ojo normal. Se receta lentes.", "Vision borrosa")
# Viernes
crear_reserva(pac_gomez, med_diaz, fecha_pasada_inicio + timedelta(days=4), time(10,0), "atendida", "Revision de tratamiento dermatologico.", "Control de acne")
crear_reserva(pac_lopez, med_diaz, fecha_pasada_inicio + timedelta(days=4), time(8,0), "atendida", "Acne juvenil. Tratamiento topico.", "Consulta por acne")
crear_reserva(pac_fernandez, med_rodriguez, fecha_pasada_inicio, time(10,0), "atendida", "Control pediatrico de rutina. Desarrollo normal.", "Control general")
crear_reserva(pac_gonzalez, med_garcia, fecha_pasada_inicio + timedelta(days=1), time(16,0), "atendida", "Papanicolaou normal.", "Control ginecologico")
crear_reserva(pac_diaz, med_lopez, fecha_pasada_inicio, time(11,0), "atendida", "Cefalea tensional. Sin signos neurologicos.", "Dolor de cabeza persistente")

# ── Reservas canceladas ─────────────────────────────────────────
fecha_futura_cercana = hoy + timedelta(days=(7 - hoy.weekday()) % 7)
# Canceladas pasadas (para historial)
crear_reserva(pac_gomez, med_fernandez, fecha_pasada_inicio + timedelta(days=2), time(8,0), "cancelada", motivo="No pude asistir")
crear_reserva(pac_gomez, med_gonzalez, fecha_pasada_inicio + timedelta(days=3), time(16,0), "cancelada", motivo="Cambio de turno")
# Canceladas futuras
crear_reserva(pac_ramirez, med_sosa, fecha_futura_cercana + timedelta(days=2), time(8,0), "cancelada", motivo="No podre asistir")
crear_reserva(pac_fernandez, med_gonzalez, fecha_futura_cercana + timedelta(days=1), time(16,0), "cancelada", motivo="Cambio de turno")

# ── Reservas activas futuras ────────────────────────────────────
# Lunes
crear_reserva(pac_gomez, med_fernandez, fecha_futura_cercana, time(8,0), "activa", motivo="Control cardiaco")
crear_reserva(pac_lopez, med_fernandez, fecha_futura_cercana, time(8,30), "activa", motivo="Electrocardiograma")
crear_reserva(pac_martinez, med_fernandez, fecha_futura_cercana, time(9,0), "activa", motivo="Dolor en el pecho")
crear_reserva(pac_gonzalez, med_fernandez, fecha_futura_cercana, time(9,30), "activa", motivo="Control de presion")
crear_reserva(pac_gomez, med_fernandez, fecha_futura_cercana, time(10,0), "activa", motivo="Colesterol alto")
# Martes
crear_reserva(pac_gomez, med_gonzalez, fecha_futura_cercana + timedelta(days=1), time(8,0), "activa", motivo="Consulta por lunar")
crear_reserva(pac_diaz, med_gonzalez, fecha_futura_cercana + timedelta(days=1), time(8,30), "activa", motivo="Control de piel")
# Miercoles
crear_reserva(pac_gomez, med_martinez, fecha_futura_cercana + timedelta(days=2), time(8,0), "activa", motivo="Dolor abdominal")
crear_reserva(pac_torres, med_rodriguez, fecha_futura_cercana, time(10,0), "activa", motivo="Control pediatrico")
# Jueves
crear_reserva(pac_gomez, med_sosa, fecha_futura_cercana + timedelta(days=3), time(9,0), "activa", motivo="Chequeo general")
crear_reserva(pac_lopez, med_garcia, fecha_futura_cercana + timedelta(days=1), time(16,0), "activa", motivo="Control ginecologico")
# Viernes
crear_reserva(pac_gomez, med_gonzalez, fecha_futura_cercana + timedelta(days=4), time(9,0), "activa", motivo="Consulta por manchas en la piel")
crear_reserva(pac_ramirez, med_lopez, fecha_futura_cercana, time(11,0), "activa", motivo="Consulta neurologica")
crear_reserva(pac_fernandez, med_ramirez, fecha_futura_cercana + timedelta(days=3), time(8,0), "activa", motivo="Control de lentes")
crear_reserva(pac_martinez, med_torres, fecha_futura_cercana + timedelta(days=2), time(9,0), "activa", motivo="Dolor de rodilla")
crear_reserva(pac_gonzalez, med_diaz, fecha_futura_cercana + timedelta(days=4), time(8,0), "activa", motivo="Consulta dermatologica")
crear_reserva(pac_diaz, med_sosa, fecha_futura_cercana + timedelta(days=2), time(8,0), "activa", motivo="Chequeo general")
crear_reserva(pac_torres, med_fernandez, fecha_futura_cercana + timedelta(days=3), time(8,0), "activa", motivo="Control cardiaco")

# ── Verificacion final ──────────────────────────────────────────
from django.contrib.auth import authenticate
user_m = authenticate(username="med_fernandez", password="med1234")
user_p = authenticate(username="pac_gomez", password="pac1234")

print("=" * 60)
print("Carga de datos de prueba completada.")
print(f"   Medicos creados: {Medico.objects.count()}")
print(f"   Pacientes creados: {Paciente.objects.count()}")
print(f"   Turnos generados: {Turno.objects.count()}")
print(f"   Reservas totales: {Reserva.objects.count()}")
print(f"     - Atendidas: {Reserva.objects.filter(estado='atendida').count()}")
print(f"     - Canceladas: {Reserva.objects.filter(estado='cancelada').count()}")
print(f"     - Activas: {Reserva.objects.filter(estado='activa').count()}")
print(f"   Autenticacion med_fernandez: {'OK' if user_m else 'FALLO'}")
print(f"   Autenticacion pac_gomez: {'OK' if user_p else 'FALLO'}")
print("=" * 60)