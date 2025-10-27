from django.db import models

# Create your models here.
class Book(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    description = models.CharField(max_length=2000)
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
        verbose_name = "Книга"
        verbose_name_plural = "Книги"