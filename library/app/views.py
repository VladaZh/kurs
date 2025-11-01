from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .forms import SignUpForm, SignInForm
from .models import Book, Article, Profile
from django.contrib.auth.decorators import login_required

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
    if request.user.is_authenticated:
        context = {
            'user': request.user,
            'is_authenticated': True
        }
        return render(request, 'app/profile.html', context)
    else:
        # Если не авторизован, перенаправляем на страницу входа
        return redirect('sign_in')

def sign_up_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Получаем данные из формы
            name = form.cleaned_data['name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Создаем username из email (убираем @ и все после)
            username = email.split('@')[0]
            
            # Проверяем, не занят ли username (если занят - добавляем число)
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name,
                last_name=last_name
            )
            
            # Авторизуем пользователя
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
            # Пробуем аутентифицировать с email как username
            user = authenticate(request, username=email, password=password)
            
            # Если не получилось, ищем пользователя по email и пробуем с его username
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
    
    # Используем отдельный шаблон для входа
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
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    user_books = profile.books.all()
    
    context = {
        'user': request.user,
        'profile': profile,
        'user_books': user_books,
        'is_authenticated': True
    }
    return render(request, 'app/profile.html', context)