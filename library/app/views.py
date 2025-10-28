from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Book
from .models import Article

def library(request):
    books = Book.objects.all()

    context = {
        'books': books,
    }
    return render(request, 'app/library.html', context)

def archive(request):
    articles = Article.objects.all()

    context = {
        'articles': articles,
    }

    return render(request, 'app/archive.html', context)

def profile(request):
    return render(request, 'app/profile.html')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    context = {
        'book': book
    }
    return render(request, 'app/book.html', context)

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    context = {
        'article': article
    }
    return render(request, 'app/article.html', context)