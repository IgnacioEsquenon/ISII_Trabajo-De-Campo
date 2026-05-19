
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home_paciente(request):
    return render(request, 'home_paciente.html')