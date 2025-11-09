from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, SignInForm
from .models import Book, Article, Profile, BookReservation, ArticleReservation
from django.http import JsonResponse, FileResponse
import boto3
from django.conf import settings
from io import BytesIO
import requests

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
    
    has_confirmed_reservation_from_others = BookReservation.objects.filter(
        book=book,
        status='reserved'
    ).exclude(user=request.user).exists() if request.user.is_authenticated else False
    
    user_reservation = None
    if request.user.is_authenticated:
        user_reservation = BookReservation.objects.filter(
            book=book, 
            user=request.user
        ).first()
    
    if not request.user.is_authenticated:
        has_confirmed_reservation_from_others = BookReservation.objects.filter(
            book=book,
            status='reserved'
        ).exists()
    
    context = {
        'book': book,
        'has_confirmed_reservation_from_others': has_confirmed_reservation_from_others,
        'user_reservation': user_reservation
    }
    return render(request, 'app/book.html', context)

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    has_confirmed_reservation_from_others = ArticleReservation.objects.filter(
        article=article,
        status='reserved'
    ).exclude(user=request.user).exists() if request.user.is_authenticated else False
    
    user_reservation = None
    if request.user.is_authenticated:
        user_reservation = ArticleReservation.objects.filter(
            article=article, 
            user=request.user
        ).first()
    
    if not request.user.is_authenticated:
        has_confirmed_reservation_from_others = ArticleReservation.objects.filter(
            article=article,
            status='reserved'
        ).exists()
    
    context = {
        'article': article,
        'has_confirmed_reservation_from_others': has_confirmed_reservation_from_others,
        'user_reservation': user_reservation
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
    
    has_confirmed_reservation_from_others = BookReservation.objects.filter(
        book=book,
        status='reserved'  
    ).exclude(user=request.user).exists()
    
    if has_confirmed_reservation_from_others:
        return redirect('book_detail', book_id=book_id)
    
    if book.quantity != 'В наличии':
        return redirect('book_detail', book_id=book_id)
    
    existing_user_reservation = BookReservation.objects.filter(
        book=book, 
        user=request.user,
        status__in=['pending', 'reserved']  
    ).first()
    
    if existing_user_reservation:
        pass
    else:
        BookReservation.objects.create(
            book=book,
            user=request.user,
            status='pending'
        )
    
    return redirect('book_detail', book_id=book_id)

@login_required
def reserve_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    has_confirmed_reservation_from_others = ArticleReservation.objects.filter(
        article=article,
        status='reserved'  
    ).exclude(user=request.user).exists()
    
    if has_confirmed_reservation_from_others:
        return redirect('article_detail', article_id=article_id)
    
    if article.quantity != 'В наличии':
        return redirect('article_detail', article_id=article_id)
    
    existing_user_reservation = ArticleReservation.objects.filter(
        article=article, 
        user=request.user,
        status__in=['pending', 'reserved']  
    ).first()
    
    if existing_user_reservation:
        pass
    else:
        ArticleReservation.objects.create(
            article=article,
            user=request.user,
            status='pending'
        )
    
    return redirect('article_detail', article_id=article_id)


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
        book=book
    ).exclude(id=reservation_id).update(status='rejected')
    
    return redirect('admin:app_bookreservation_changelist')

@login_required
def complete_reservation(request, reservation_id):
    if not request.user.is_staff:
        return redirect('library')
    
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    reservation.remove_book_from_profile()
    
    reservation.status = 'completed'
    reservation.save()
    
    book = reservation.book
    book.quantity = 'В наличии'
    book.save()
    
    return redirect('admin:app_bookreservation_changelist')

@login_required
def approve_reservation_article(request, reservation_id):
    if not request.user.is_staff:
        return redirect('archive')
    
    reservation = get_object_or_404(ArticleReservation, id=reservation_id)
    
    reservation.status = 'reserved'
    reservation.save()  
    
    article = reservation.article
    article.quantity = 'Нет в наличии'
    article.save()
    
    ArticleReservation.objects.filter(
        article=article
    ).exclude(id=reservation_id).update(status='rejected')
    
    return redirect('admin:app_articlereservation_changelist')

@login_required
def complete_reservation_article(request, reservation_id):
    if not request.user.is_staff:
        return redirect('archive')
    
    reservation = get_object_or_404(ArticleReservation, id=reservation_id)
    reservation.remove_article_from_profile()
    
    reservation.status = 'completed'
    reservation.save()
    
    article = reservation.article
    article.quantity = 'В наличии'
    article.save()
    
    return redirect('admin:app_articlereservation_changelist')

def custom_logout(request):
    logout(request)
    return redirect('sign_in')


def download_book(request, book_id):
    try:
        book = Book.objects.get(id=book_id)
        response = FileResponse(book.pdf_file.open(), filename=book.title + '.pdf')
        return response
    except Book.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)

@login_required
def read_book_pdf(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    user_reservation = BookReservation.objects.filter(
        book=book, 
        user=request.user, 
        status='reserved'
    ).first()
    
    if not user_reservation or not book.pdf_file:
        raise Http404("Доступ запрещен или файл не найден")

    try:
        correct_url = f"https://fb57c80b9e3bd4a806cf8708ddaf711b.bckt.ru/{book.pdf_file.name}"
        
        response = requests.get(correct_url, timeout=30)
        response.raise_for_status()
        
        file_response = HttpResponse(
            response.content,
            content_type='application/pdf'
        )
        file_response['Content-Disposition'] = f'inline; filename="{book.title}.pdf"'
        return file_response
        
    except requests.RequestException as e:
        raise Http404(f"Не удалось загрузить файл: {str(e)}")
    
@login_required
def read_article_pdf(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    user_reservation = ArticleReservation.objects.filter(
        article=article, 
        user=request.user, 
        status='reserved'
    ).first()
    
    if not user_reservation or not article.pdf_file:
        raise Http404("Доступ запрещен или файл не найден")

    try:
        file_name = article.pdf_file.name
        if not file_name.startswith('articles/'):
            file_name = f'articles/{file_name}'
        correct_url = f"https://fb57c80b9e3bd4a806cf8708ddaf711b.bckt.ru/{file_name}"
        
        response = requests.get(correct_url, timeout=30)
        response.raise_for_status()
        
        file_response = HttpResponse(
            response.content,
            content_type='application/pdf'
        )
        file_response['Content-Disposition'] = f'inline; filename="{article.title}.pdf"'
        return file_response
        
    except requests.RequestException as e:
        raise Http404(f"Не удалось загрузить файл: {str(e)}")