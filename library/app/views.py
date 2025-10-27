from django.shortcuts import render
from django.http import HttpResponse
from .models import Book

def library(request):
    books = Book.objects.all()

    context = {
        'books': books,
    }
    return render(request, 'app/library.html', context)

def archive(request):
    return render(request, 'app/archive.html')

def profile(request):
    return render(request, 'app/profile.html')