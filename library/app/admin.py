from django.contrib import admin
from .models import Book, Profile
from .models import Article
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    # Показываем связанные книги через фильтрацию
    filter_horizontal = ['books']  # Для ManyToManyField
    extra = 0

# Кастомный UserAdmin для отображения профиля
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Book)
admin.site.register(Article)