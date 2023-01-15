from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=250,
        null=False,
        blank=False,
        verbose_name='Ingredient name'
        )
    measurement_unit = models.CharField(
        max_length=100,
        verbose_name='Measurement unit'
    )

    def __repr__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
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
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredients'
    )
    times_bookmarked = models.PositiveIntegerField('Times bookmarked')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']


class Tag(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Tag name',
        blank=False,
        null=False,
        unique=True
    )
    color = models.CharField(
        max_length=7,
        verbose_name='color',
        blank=False,
        null=False,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='slug',
        blank=False,
        null=False,
        unique=True
    )
    recipe = models.ManyToManyField(Recipe, related_name='tags', blank=True)

    def __repr___(self):
        return self.name


class RecipeIngredients(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Ingredient amount')

    def __repr__(self):
        return f'{self.ingredient} for {self.recipe}'
