from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.html import mark_safe
from django.core.cache import cache

User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        max_length=200, verbose_name='Tag name', unique=True
    )
    color = models.CharField(
        max_length=7,
        verbose_name='color',
        unique=True,
        validators=[
            RegexValidator(
                regex='^#[A-Fa-f0-9]{6}$',
                message='Incorrect HEX color.',
                code='incorrect_hex_color',
            )
        ],
    )
    slug = models.SlugField(verbose_name='slug', unique=True, max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=250, verbose_name='Ingredient name', db_index=True
    )
    measurement_unit = models.CharField(
        max_length=100, verbose_name='Measurement unit'
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='Unique name and measurement units combo',
            ),
        ]


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    name = models.CharField(max_length=200, verbose_name='name')
    image = models.ImageField(
        'Picture', upload_to='recipes/', blank=False, null=False
    )
    text = models.TextField('Cooking algorithm')
    pub_date = models.DateTimeField(
        'Publication_date', auto_now_add=True, db_index=True
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Cooking Time',
        validators=(MinValueValidator(limit_value=1),),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        blank=False,
        verbose_name='Ingredients',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', blank=True, verbose_name='Tags'
    )

    def image_display(self):
        return mark_safe(f'<img src="{(self.image.url)}" width="150" />')

    def __str__(self):
        return self.name

    @property
    def favorited(self):
        favorited = cache.get(f'{self.id}_favorited')
        if favorited is None:
            favorited = Favorite.objects.filter(recipe=self).count()
            cache.set(
                f'{self.id}_favorited',
                favorited,
                settings.FAVORITED_CACHE_SECONDS_TTL,
            )
        return favorited

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-pub_date']


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name='recipeingredients', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name='recipeingredients', on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(verbose_name='Ingredient amount')

    def __str__(self):
        return (
            f'{self.ingredient.name}, {self.amount} '
            f'{self.ingredient.measurement_unit} for {self.recipe}'
        )

    class Meta:
        verbose_name = 'Recipe Ingredient'
        verbose_name_plural = 'Recipe Ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='Unique ingredient for a recipe',
            ),
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Bookmarking user',
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Favorited recipe',
    )

    def __str__(self):
        return f'{self.user} bookmark on {self.recipe}'

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='Unique user-recipe bookmark'
            ),
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_cart',
        verbose_name='Shopping cart user',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_cart',
        verbose_name='Recipe in shopping cart',
    )

    def __str__(self):
        return f'{self.recipe} in {self.user} cart'

    class Meta:
        verbose_name = 'Shopping cart'
        verbose_name_plural = 'Shopping carts'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='Unique user and recipe in cart',
            ),
        ]
