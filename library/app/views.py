from django.shortcuts import render
from django.http import HttpResponse
from .models import Book
from django.shortcuts import render, get_object_or_404

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

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    context = {
        'book': book
    }
    return render(request, 'app/book.html', context)