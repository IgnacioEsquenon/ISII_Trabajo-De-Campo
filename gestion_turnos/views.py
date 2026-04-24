from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth import login
from .models import Medico, BloqueHorario
from .forms import RegistroMedicoForm, RegistroPacienteForm
from .forms import BloqueHorarioForm 
from datetime import date, datetime, timedelta
from .models import Turno

def home_principal(request):
    # Si el usuario ya está logueado, lo mandamos a su panel
    if request.user.is_authenticated:
       # 2. ¿Es un médico? 
        # (Django crea automáticamente la propiedad 'medico' en el user por la relación 1 a 1)
        if hasattr(request.user, 'medico'):
            # Si tiene perfil de médico, lo mandamos directo a su agenda
            return redirect('agenda_medico', medico_id=request.user.medico.id)
        
        # 3. Si no es médico, asumimos que es paciente
        else:
            return redirect('home_paciente')
        
    return render(request, 'home_principal.html')

def seleccionar_registro(request):
    # Si el usuario ya está logueado, no tiene sentido que se registre
    if request.user.is_authenticated:
        return redirect('home')
        
    return render(request, 'seleccionar_registro.html')

def registro_medico(request):
    # Si ya está logueado, lo pateamos a su home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroMedicoForm(request.POST)
        if form.is_valid():
            # Esto dispara el def save() gigante en forms.py
            user = form.save() 
            
            # Autologueo de Django
            login(request, user) 
            
            # Como ahora es medico, el semáforo lo va a derivar a su agenda
            return redirect('home')
    else:
        form = RegistroMedicoForm()

    return render(request, 'registro_medico.html', {'form': form})

def registro_paciente(request):
    # Si ya está logueado, al semáforo central
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user) # Autologueo
            
            # lo va a derivar a la vista del paciente en construccion (home_paciente.html)
            return redirect('home')
    else:
        form = RegistroPacienteForm()

    return render(request, 'registro_paciente.html', {'form': form})

 
@login_required
def agenda_medico(request, medico_id):
    # El médico solo ve su propia agenda
    medico = get_object_or_404(Medico, pk=medico_id, user=request.user)
    bloques = medico.bloques.all() 

    turnos_por_fecha = {}

    # Logica para mostrar turnos existentes 
    # Esto hace que la agenda no aparezca vacía si ya hay turnos creados
    hoy = date.today()
    turnos_db = Turno.objects.filter(
        bloque__medico=medico, 
        fecha__gte=hoy
    ).order_by('fecha', 'hora')

    for t in turnos_db:
        if t.fecha not in turnos_por_fecha:
            turnos_por_fecha[t.fecha] = []
        turnos_por_fecha[t.fecha].append(t)

    if request.method == 'POST':
        form = BloqueHorarioForm(request.POST)
        if form.is_valid():
            bloque = form.save(commit=False)
            bloque.medico = medico
            
            try:
                bloque.full_clean() # Esto ejecuta el def clean() del models.py
                bloque.save()

                generar_turnos_automaticos(bloque) # Generamos los turnos automáticamente al crear el bloque
                messages.success(request, 'Bloque y turnos creados correctamente.')
                return redirect('agenda_medico', medico_id=medico.id)
            except ValidationError as e:
                # Si falla la validación, le pasamos el error al formulario
                form.add_error(None, e) 
    else:
        form = BloqueHorarioForm()

    bloques_por_dia = {}
    for b in bloques:
        dia = b.get_dia_semana_display()
        bloques_por_dia.setdefault(dia, []).append(b)

    return render(request, 'agenda_medico.html', {
        'medico':         medico,
        'form':           form,
        'bloques_por_dia': bloques_por_dia,
        'turnos_por_fecha': turnos_por_fecha,
    })



def eliminar_bloque(request, bloque_id):
    bloque    = get_object_or_404(BloqueHorario, pk=bloque_id)
    medico_id = bloque.medico.id
    bloque.delete()
    messages.success(request, 'Bloque eliminado.')
    return redirect('agenda_medico', medico_id=medico_id)

def generar_turnos_automaticos(bloque, semanas_a_generar=4):
    hoy = date.today()
    
    # Encontrar la próxima fecha real que coincida con el día de la semana del bloque
    dias_para_el_proximo = (bloque.dia_semana - hoy.weekday()) % 7
    proxima_fecha = hoy + timedelta(days=dias_para_el_proximo)
    
    # Armamos una lista con las fechas exactas (ej: como un mes tiene 4 semanas, generamos 4 fechas)
    fechas = [proxima_fecha + timedelta(weeks=i) for i in range(semanas_a_generar)]
    
    # Matematicas niño (Dividir el bloque en turnos)
    inicio_dt = datetime.combine(hoy, bloque.hora_inicio)
    fin_dt = datetime.combine(hoy, bloque.hora_fin)
    
    turnos_a_crear = []
    
    for fecha_exacta in fechas:
        tiempo_actual = inicio_dt
        
        # Mientras el inicio del turno + la duración no supere la hora de fin del bloque
        while (tiempo_actual + timedelta(minutes=bloque.duracion_turno)) <= fin_dt:
            turnos_a_crear.append(
                Turno(
                    bloque=bloque,
                    fecha=fecha_exacta,
                    hora=tiempo_actual.time(),
                    estado='disponible'
                )
            )
            # Avanza el reloj a la siguiente franja (pasar de 10 a 10:30 por ej)
            tiempo_actual += timedelta(minutes=bloque.duracion_turno)
            
    if turnos_a_crear:
        Turno.objects.bulk_create(turnos_a_crear)
