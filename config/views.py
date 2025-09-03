# Homepage views for the project
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
