from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import User


class Category(models.Model):
    name = models.CharField(verbose_name='Название', max_length=256)
    slug = models.SlugField(verbose_name='Идентификатор', max_length=50,
                            unique=True
                            )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Genre(models.Model):
    name = models.CharField(verbose_name='Название', max_length=256)
    slug = models.SlugField(verbose_name='Идентификатор', max_length=50,
                            unique=True
                            )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Title(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    year = models.IntegerField(verbose_name='Дата',)
    description = models.TextField(verbose_name='Описание', blank=True,
                                   null=True)
    genre = models.ManyToManyField(Genre, verbose_name='Жанр',
                                   through='TitleGenre')
    category = models.ForeignKey(Category, verbose_name='Категория',
                                 on_delete=models.CASCADE,
                                 related_name='titles',)
    rating = models.IntegerField(verbose_name='Рейтинг', null=True,)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class TitleGenre(models.Model):
    title = models.ForeignKey(Title, verbose_name='Наименование',
                              on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, verbose_name='Жанр',
                              on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title}_{self.genre}'


class Review(models.Model):
    """Текстовые отзывы на произведения и оценки от 1 до 10."""
    title = models.ForeignKey(
        Title,
        verbose_name='Произведение',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    score = models.PositiveSmallIntegerField(
        verbose_name='Рейтинг',
        validators=[
            MinValueValidator(1, 'Выберите значение от 1 до 10!'),
            MaxValueValidator(10, 'Выберите значение от 1 до 10!')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['pub_date']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_review'
            ),
        ]


class Comment(models.Model):
    """Комментарии к отзывам."""
    review = models.ForeignKey(
        Review,
        verbose_name='Отзыв',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['pub_date']
