from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

class Book(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name='Название')
    author = models.CharField(max_length=50, verbose_name='Автор')
    description_short = models.TextField(verbose_name='Краткое описание')
    description_long = models.TextField(verbose_name='Подробное описание')
    year = models.IntegerField(verbose_name='Год издания')
    quantity = models.CharField(
        max_length=13,
        verbose_name="В наличии",
        choices=[
            ('В наличии', 'В наличии'),
            ('Нет в наличии', 'Нет в наличии')
        ]
    )
    genre = models.CharField(
        max_length=100, 
        verbose_name="Жанр",
        choices=[
            ('Художественные', 'Художественные'),
            ('Научные', 'Научные'),
            ('Исторические', 'Исторические'),
            ('Образовательные', 'Образовательные'),
        ]
    )

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "книга"
        verbose_name_plural = "книги"

class Article(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name='Название')
    author = models.CharField(max_length=50, verbose_name='Автор')
    description_short = models.TextField(verbose_name='Краткое описание')
    description_long = models.TextField(verbose_name='Подробное описание')
    year = models.IntegerField(verbose_name='Год публикации')
    quantity = models.CharField(
        max_length=13,
        verbose_name="В наличии",
        choices=[
            ('В наличии', 'В наличии'),
            ('Нет в наличии', 'Нет в наличии')
        ]
    )
    genre = models.CharField(
        max_length=100, 
        verbose_name="Жанр",
        choices=[
            ('Технические', 'Технические'),
            ('Медицинские', 'Медицинские'),
            ('Химические', 'Химические'),
            ('Гуманитарные', 'Гуманитарные'),
        ]
    )

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "статья"
        verbose_name_plural = "статьи"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    books = models.ManyToManyField('Book', blank=True, related_name='profiles')
    articles = models.ManyToManyField('Article', blank=True, related_name='profiles')

    def __str__(self):
        return f"{self.user.username} Profile"
    
    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class BookReservation(models.Model):
    STATUS_CHOICES = [
        ('reserved', 'Забронирована'),
        ('pending', 'Ожидает подтверждения'),
        ('rejected', 'Отклонена'),
        ('completed', 'Завершена'),
    ]
    book = models.ForeignKey('Book', on_delete=models.CASCADE, verbose_name='Книга', editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', editable=False)
    status = models.CharField(max_length=21, default="pending", verbose_name='Статус', choices=STATUS_CHOICES)


    def __str__(self):
        return f"Бронь {self.book.title} - {self.user.username}"
    
    class Meta:
        verbose_name = 'заявка на бронь'
        verbose_name_plural = 'заявки на бронь'
