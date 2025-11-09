from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

class BookS3Storage(S3Boto3Storage):
    location = 'books'

class ArticleS3Storage(S3Boto3Storage):
    location = 'articles'

class Book(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name='Название')
    author = models.CharField(max_length=50, verbose_name='Автор')
    description_short = models.TextField(verbose_name='Краткое описание')
    description_long = models.TextField(verbose_name='Подробное описание')
    year = models.IntegerField(verbose_name='Год издания')
    pdf_file = models.FileField(
        upload_to='',
        verbose_name='PDF файл',
        blank=True,
        null=True,
        storage=BookS3Storage(),
    )
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

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            storage = self.pdf_file.storage
            file_name = self.pdf_file.name
            
            super().delete(*args, **kwargs)
            
            try:
                if storage.exists(file_name):
                    storage.delete(file_name)
            except Exception as e:
                print(f"Ошибка при удалении файла из S3: {e}")
        else:
            super().delete(*args, **kwargs)

    def get_correct_pdf_url(self):
        if self.pdf_file:
            old_url = self.pdf_file.url
            correct_url = old_url.replace(
                'https://s3.buckets.ru/library/', 
                'https://fb57c80b9e3bd4a806cf8708ddaf711b.bckt.ru/'
            )
            return correct_url
        return None

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "книга"
        verbose_name_plural = "книги"

@receiver(post_delete, sender=Book)
def delete_book_file(sender, instance, **kwargs):
    if instance.pdf_file:
        try:
            storage = instance.pdf_file.storage
            file_name = instance.pdf_file.name
            
            if storage.exists(file_name):
                storage.delete(file_name)
                print(f"Файл {file_name} удален из S3")
        except Exception as e:
            print(f"Ошибка при удалении файла из S3: {e}")

class Article(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name='Название')
    author = models.CharField(max_length=50, verbose_name='Автор')
    description_short = models.TextField(verbose_name='Краткое описание')
    description_long = models.TextField(verbose_name='Подробное описание')
    year = models.IntegerField(verbose_name='Год публикации')
    pdf_file = models.FileField(
        upload_to='',
        verbose_name='PDF файл',
        blank=True,
        null=True,
        storage=ArticleS3Storage,
    )
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

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            storage = self.pdf_file.storage
            file_name = self.pdf_file.name
            
            super().delete(*args, **kwargs)
            
            try:
                if storage.exists(file_name):
                    storage.delete(file_name)
            except Exception as e:
                print(f"Ошибка при удалении файла из S3: {e}")
        else:
            super().delete(*args, **kwargs)

    def get_correct_pdf_url(self):
        if self.pdf_file:
            old_url = self.pdf_file.url
            correct_url = old_url.replace(
                'https://s3.buckets.ru/library/', 
                'https://fb57c80b9e3bd4a806cf8708ddaf711b.bckt.ru/'
            )
            return correct_url
        return None

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "статья"
        verbose_name_plural = "статьи"

@receiver(post_delete, sender=Article)
def delete_article_file(sender, instance, **kwargs):
    if instance.pdf_file:
        try:
            storage = instance.pdf_file.storage
            file_name = instance.pdf_file.name
            
            if storage.exists(file_name):
                storage.delete(file_name)
                print(f"Файл {file_name} удален из S3")
        except Exception as e:
            print(f"Ошибка при удалении файла из S3: {e}")

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
    
    def save(self, *args, **kwargs):
        
        if self.pk:
            old_status = BookReservation.objects.get(pk=self.pk).status
            if old_status != 'reserved' and self.status == 'reserved':
                self.add_book_to_profile()
        
        super().save(*args, **kwargs)
    
    def add_book_to_profile(self):
        profile, created = Profile.objects.get_or_create(user=self.user)
        profile.books.add(self.book)
    
    def remove_book_from_profile(self):
        profile = getattr(self.user, 'profile', None)
        if profile:
            profile.books.remove(self.book)
    
    class Meta:
        verbose_name = 'заявка на бронь книги'
        verbose_name_plural = 'заявки на бронь книг'

class ArticleReservation(models.Model):
    STATUS_CHOICES = [
        ('reserved', 'Забронирована'),
        ('pending', 'Ожидает подтверждения'),
        ('rejected', 'Отклонена'),
        ('completed', 'Завершена'),
    ]
    article = models.ForeignKey('Article', on_delete=models.CASCADE, verbose_name='Статья', editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', editable=False)
    status = models.CharField(max_length=21, default="pending", verbose_name='Статус', choices=STATUS_CHOICES)

    def __str__(self):
        return f"Бронь {self.article.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        
        if self.pk:
            old_status = ArticleReservation.objects.get(pk=self.pk).status
            if old_status != 'reserved' and self.status == 'reserved':
                self.add_article_to_profile()
        
        super().save(*args, **kwargs)
    
    def add_article_to_profile(self):
        profile, created = Profile.objects.get_or_create(user=self.user)
        profile.articles.add(self.article)
    
    def remove_article_from_profile(self):
        profile = getattr(self.user, 'profile', None)
        if profile:
            profile.articles.remove(self.article)
    
    class Meta:
        verbose_name = 'заявка на бронь статьи'
        verbose_name_plural = 'заявки на бронь статей'
