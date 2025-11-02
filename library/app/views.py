from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, SignInForm
from .models import Book, Article, Profile, BookReservation
from django.contrib import messages

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
    
    has_active_reservation_from_others = BookReservation.objects.filter(
        book=book,
        status__in=['reserved', 'pending']
    ).exclude(user=request.user).exists() if request.user.is_authenticated else False
    
    user_reservation = None
    if request.user.is_authenticated:
        user_reservation = BookReservation.objects.filter(
            book=book, 
            user=request.user
        ).first()
    
    if not request.user.is_authenticated:
        has_active_reservation_from_others = BookReservation.objects.filter(
            book=book,
            status__in=['reserved', 'pending']
        ).exists()
    
    context = {
        'book': book,
        'has_active_reservation_from_others': has_active_reservation_from_others,
        'user_reservation': user_reservation
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

@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    has_active_reservation_from_others = BookReservation.objects.filter(
        book=book,
        status__in=['reserved', 'pending']  
    ).exclude(user=request.user).exists()
    
    if has_active_reservation_from_others:
        return redirect('book_detail', book_id=book_id)
    
    if book.quantity != 'В наличии':
        return redirect('book_detail', book_id=book_id)
    
    user_reservation = BookReservation.objects.filter(
        book=book, 
        user=request.user
    ).first()
    
    if user_reservation:
        user_reservation.status = 'pending'
        user_reservation.save()
    else:
        BookReservation.objects.create(
            book=book,
            user=request.user,
            status='pending'
        )
    
    return redirect('book_detail', book_id=book_id)

@login_required
def approve_reservation(request, reservation_id):
    if not request.user.is_staff:
        return redirect('library')
    
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    
    reservation.status = 'reserved'
    reservation.save()
    
    book = reservation.book
    book.quantity = 'Нет в наличии'
    book.save()
    
    BookReservation.objects.filter(
        book=book,
        status='pending'
    ).exclude(id=reservation_id).update(status='rejected')
    
    messages.success(request, f'Бронь книги "{book.title}" подтверждена')
    return redirect('admin:app_bookreservation_changelist')

@login_required
def complete_reservation(request, reservation_id):
    if not request.user.is_staff:
        return redirect('library')
    
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    
    reservation.status = 'completed'
    reservation.save()
    
    book = reservation.book
    book.quantity = 'В наличии'
    book.save()
    
    messages.success(request, f'Бронь книги "{book.title}" завершена')
    return redirect('admin:app_bookreservation_changelist')