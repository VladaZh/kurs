from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, SignInForm
from .models import Book, Article, Profile

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

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    user_books = profile.books.all()
    user_articles = profile.articles.all()
    
    context = {
        'user': request.user,
        'profile': profile,
        'user_books': user_books,
        'user_articles': user_articles,
        'is_authenticated': True
    }
    return render(request, 'app/profile.html', context)

def sign_up_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
                last_name=last_name
            )
            
            login(request, user)
            return redirect('profile')
    else:
        form = SignUpForm()
    
    context = {
        'form': form,
    }
    return render(request, 'app/sign_up.html', context)

def sign_in_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    error = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            error = 'Пожалуйста, заполните все поля'
        else:
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                try:
                    user_obj = User.objects.get(email=email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                return redirect('profile')
            else:
                error = 'Неверный email или пароль'
    
    return render(request, 'app/sign_in.html', {'error': error})

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

@login_required
def add_book_to_profile(request, book_id):
    profile, created = Profile.objects.get_or_create(user=request.user)
    book = get_object_or_404(Book, id=book_id)
    
    profile.books.add(book)
    
    return redirect('library')

@login_required
def add_article_to_profile(request, article_id):
    profile, created = Profile.objects.get_or_create(user=request.user)
    article = get_object_or_404(Article, id=article_id)
    
    profile.articles.add(article)
    
    return redirect('archive')

@login_required
def remove_book_from_profile(request, book_id):
    profile, created = Profile.objects.get_or_create(user=request.user)
    book = get_object_or_404(Book, id=book_id)
    
    profile.books.remove(book)
    
    return redirect('profile')

@login_required
def remove_article_from_profile(request, article_id):
    profile, created = Profile.objects.get_or_create(user=request.user)
    article = get_object_or_404(Article, id=article_id)
    
    profile.articles.remove(article)
    
    return redirect('profile')