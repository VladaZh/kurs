from django.contrib import admin
from django.urls import path
from .models import Book, Profile, Article, BookReservation, ArticleReservation
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from app.tasks import send_approval_notification, schedule_return_reminder

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    filter_horizontal = ['books', 'articles']
    extra = 0

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']

class BookReservationInline(admin.TabularInline):
    model = BookReservation
    extra = 0
    readonly_fields = ['user', 'status'] 
    can_delete = False
    show_change_link = True

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'quantity', 'genre']
    list_filter = ['quantity', 'genre']
    search_fields = ['title', 'author']
    inlines = [BookReservationInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'description_short', 'description_long', 'year', 'genre', 'pdf_file', 'quantity')
        }),
    )

class ArticleReservationInline(admin.TabularInline):
    model = ArticleReservation
    extra = 0
    readonly_fields = ['user', 'status'] 
    can_delete = False
    show_change_link = True

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'quantity', 'genre']
    list_filter = ['quantity', 'genre']
    search_fields = ['title', 'author']
    inlines = [ArticleReservationInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'description_short', 'description_long', 'year', 'genre', 'pdf_file', 'quantity')
        }),
    )

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ['book', 'get_user', 'status', 'quick_actions'] 
    list_filter = ['status'] 
    list_editable = ['status']
    search_fields = ['book__title', 'user__username']
    readonly_fields = ['book', 'user'] 
    actions = ['approve_selected', 'reject_selected', 'complete_selected']
    
    def get_user(self, obj):
        return obj.user.username
    get_user.short_description = 'Пользователь'
    get_user.admin_order_field = 'user__username'
    
    def quick_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Одобрить</a> ',
                reverse('admin:app_bookreservation_approve', args=[obj.id])
            )
        elif obj.status == 'reserved':
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745;">Завершить</a>',
                reverse('admin:app_bookreservation_complete', args=[obj.id])
            )
        return '-'
    quick_actions.short_description = 'Быстрые действия'
    
    def approve_selected(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'pending':
                self._approve_reservation(reservation)
        self.message_user(request, f"Одобрено {queryset.count()} броней")
    approve_selected.short_description = "Одобрить выбранные брони"
    
    def reject_selected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"Отклонено {updated} броней")
    reject_selected.short_description = "Отклонить выбранные брони"
    
    def complete_selected(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'reserved':
                self._complete_reservation(reservation)
        self.message_user(request, f"Завершено {queryset.count()} броней")
    complete_selected.short_description = "Завершить выбранные брони"
    
    def _approve_reservation(self, reservation):
        reservation.status = 'reserved'
        reservation.save()
        book = reservation.book
        book.quantity = 'Нет в наличии'
        book.save()
        BookReservation.objects.filter(
            book=book
        ).exclude(id=reservation.id).update(status='rejected')
        try:
            send_approval_notification.delay(
                book_title=book.title,
                user_email=reservation.user.email,
                first_name=reservation.user.first_name,
                last_name=reservation.user.last_name
            )
            
            schedule_return_reminder.delay(
                book_title=book.title,
                user_email=reservation.user.email,
                first_name=reservation.user.first_name,
                last_name=reservation.user.last_name
            )
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    
    def _complete_reservation(self, reservation):
        reservation.status = 'completed'
        reservation.save()
        book = reservation.book
        book.quantity = 'В наличии'
        book.save()
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/approve/',
                self.admin_site.admin_view(self.approve_reservation),
                name='app_bookreservation_approve',
            ),
            path(
                '<path:object_id>/complete/',
                self.admin_site.admin_view(self.complete_reservation),
                name='app_bookreservation_complete',
            ),
        ]
        return custom_urls + urls
    
    def approve_reservation(self, request, object_id):
        reservation = BookReservation.objects.get(id=object_id)
        if reservation.status == 'pending':
            self._approve_reservation(reservation)
            self.message_user(request, f"Бронь книги '{reservation.book.title}' одобрена")
        return HttpResponseRedirect(reverse('admin:app_bookreservation_changelist'))
    
    def complete_reservation(self, request, object_id):
        reservation = BookReservation.objects.get(id=object_id)
        if reservation.status == 'reserved':
            self._complete_reservation(reservation)
            self.message_user(request, f"Бронь книги '{reservation.book.title}' завершена")
        return HttpResponseRedirect(reverse('admin:app_bookreservation_changelist'))
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'user')

@admin.register(ArticleReservation)
class ArticleReservationAdmin(admin.ModelAdmin):
    list_display = ['article', 'get_user', 'status', 'quick_actions'] 
    list_filter = ['status'] 
    list_editable = ['status']
    search_fields = ['article__title', 'user__username']
    readonly_fields = ['article', 'user'] 
    actions = ['approve_selected', 'reject_selected', 'complete_selected']
    
    def get_user(self, obj):
        return obj.user.username
    get_user.short_description = 'Пользователь'
    get_user.admin_order_field = 'user__username'
    
    def quick_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Одобрить</a> ',
                reverse('admin:app_articlereservation_approve', args=[obj.id])
            )
        elif obj.status == 'reserved':
            return format_html(
                '<a class="button" href="{}" style="background-color: #28a745;">Завершить</a>',
                reverse('admin:app_articlereservation_complete', args=[obj.id])
            )
        return '-'
    quick_actions.short_description = 'Быстрые действия'
    
    def approve_selected(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'pending':
                self._approve_reservation(reservation)
        self.message_user(request, f"Одобрено {queryset.count()} броней")
    approve_selected.short_description = "Одобрить выбранные брони"
    
    def reject_selected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"Отклонено {updated} броней")
    reject_selected.short_description = "Отклонить выбранные брони"
    
    def complete_selected(self, request, queryset):
        for reservation in queryset:
            if reservation.status == 'reserved':
                self._complete_reservation(reservation)
        self.message_user(request, f"Завершено {queryset.count()} броней")
    complete_selected.short_description = "Завершить выбранные брони"
    
    def _approve_reservation(self, reservation):
        reservation.status = 'reserved'
        reservation.save()
        article = reservation.article
        article.quantity = 'Нет в наличии'
        article.save()
        ArticleReservation.objects.filter(
            article=article
        ).exclude(id=reservation.id).update(status='rejected')
        try:
            send_approval_notification.delay(
                book_title=article.title,
                user_email=reservation.user.email,
                first_name=reservation.user.first_name,
                last_name=reservation.user.last_name
            )
            
            schedule_return_reminder.delay(
                book_title=article.title,
                user_email=reservation.user.email,
                first_name=reservation.user.first_name,
                last_name=reservation.user.last_name
            )
        except Exception as e:
            print(f"Ошибка при отправке уведомления: {e}")
    
    def _complete_reservation(self, reservation):
        reservation.status = 'completed'
        reservation.save()
        article = reservation.article
        article.quantity = 'В наличии'
        article.save()
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/approve/',
                self.admin_site.admin_view(self.approve_reservation),
                name='app_articlereservation_approve',
            ),
            path(
                '<path:object_id>/complete/',
                self.admin_site.admin_view(self.complete_reservation),
                name='app_articlereservation_complete',
            ),
        ]
        return custom_urls + urls
    
    def approve_reservation(self, request, object_id):
        reservation = ArticleReservation.objects.get(id=object_id)
        if reservation.status == 'pending':
            self._approve_reservation(reservation)
            self.message_user(request, f"Бронь статьи '{reservation.article.title}' одобрена")
        return HttpResponseRedirect(reverse('admin:app_articlereservation_changelist'))
    
    def complete_reservation(self, request, object_id):
        reservation = ArticleReservation.objects.get(id=object_id)
        if reservation.status == 'reserved':
            self._complete_reservation(reservation)
            self.message_user(request, f"Бронь статьи '{reservation.article.title}' завершена")
        return HttpResponseRedirect(reverse('admin:app_articlereservation_changelist'))
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('article', 'user')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)