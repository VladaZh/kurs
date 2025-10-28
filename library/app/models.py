from django.db import models

# Create your models here.
class Book(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name='Название')
    author = models.CharField(max_length=50, verbose_name='Автор')
    description_short = models.TextField(verbose_name='Краткое описание')
    description_long = models.TextField(verbose_name='Подробное описание')
    year = models.IntegerField(verbose_name='Год издания')
    quantity = models.IntegerField(verbose_name='В наличии')
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
    quantity = models.IntegerField(verbose_name='В наличии')
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