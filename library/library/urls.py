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
    path('sign-in/', views.sign_in_view, name='sign_in'),  # отдельная страница входа
    path('logout/', auth_views.LogoutView.as_view(next_page='library'), name='logout'),
]
