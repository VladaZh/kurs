from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from app import views

urlpatterns = [
    path('', views.library, name='library'),
    path('archive/', views.archive, name='archive'),
    path('profile/', views.profile, name='profile'),
    path('admin/', admin.site.urls),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('sign-up/', views.sign_up_view, name='sign_up'),
    path('sign-in/', views.sign_in_view, name='sign_in'),
    path('logout/', views.custom_logout, name='logout'),
    path('book/<int:book_id>/reserve/', views.reserve_book, name='reserve_book'),
    path('article/<int:article_id>/reserve/', views.reserve_article, name='reserve_article'),
    path('book/<int:book_id>/remove/', views.remove_book_from_profile, name='remove_book_from_profile'),
    path('article/<int:article_id>/remove/', views.remove_article_from_profile, name='remove_article_from_profile'),
    
    path('book/<int:book_id>/add/', views.add_book_to_profile, name='add_book_to_profile'),
    path('article/<int:article_id>/add/', views.add_article_to_profile, name='add_article_to_profile'),
    path('book/<int:book_id>/read-pdf/', views.read_book_pdf, name='read_book_pdf'),
]
