from django.shortcuts import render
from django.http import HttpResponse

def library(request):
    return render(request, 'app/library.html')

def archive(request):
    return render(request, 'app/archive.html')

def profile(request):
    return render(request, 'app/profile.html')