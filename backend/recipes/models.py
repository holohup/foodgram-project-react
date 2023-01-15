from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingridient(models.Model):
    name = models.CharField(
        max_length=250,
        null=False,
        blank=False,
        verbose_name='Ingridient name'
        )
    measurement = models.CharField(
        max_length=100,
        verbose_name='Measurement unit'
    )

    def __str__(self):
        return f'{self.name}, {self.measurement}'

    class Meta:
        verbose_name = 'Ingridient'
        verbose_name_plural = 'Ingridients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement'],
                name='Unique name and measurement units combo'
            ),
        ]


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(
        'Picture',
        upload_to='recipes/',
        blank=False,
        null=False
    )
    text = models.TextField('Cooking algorithm')
    pub_date = models.DateTimeField(
        'Publication_date',
        auto_now_add=True,
        db_index=True
    )
    cooking_time = models.PositiveIntegerField(verbose_name='Cooking Time')
    ingridients = models.ManyToManyField(
        Ingridient, through='RecipeIngridients'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']


class Tag(models.Model):
    name = models.CharField(max_length=64, verbose_name='Tag name')
    color = models.CharField(max_length=7, verbose_name='color')
    slug = models.SlugField(verbose_name='slug')
    recipe = models.ManyToManyField(Recipe)


class RecipeIngridients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingridient = models.ForeignKey(Ingridient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Ingridient amount')

    def __str__(self):
        return f'{self.ingridient} for {self.recipe}'
