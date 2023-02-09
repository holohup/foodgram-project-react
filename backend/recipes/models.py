from django.conf import settings
from django.core.cache import cache
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.html import mark_safe

from users.models import User


class Tag(models.Model):
    """Tag model."""

    name = models.CharField(
        max_length=200, verbose_name='Tag name', unique=True
    )
    color = models.CharField(
        max_length=7,
        verbose_name='color',
        unique=True,
        validators=(
            RegexValidator(
                regex='^#[A-Fa-f0-9]{6}$',
                message='Incorrect HEX color.',
                code='incorrect_hex_color',
            ),
        ),
    )
    slug = models.SlugField(verbose_name='slug', unique=True, max_length=200)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient model."""

    name = models.CharField(
        max_length=250,
        verbose_name='Ingredient name',
    )
    measurement_unit = models.CharField(
        max_length=100, verbose_name='Measurement unit'
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='Unique name and measurement units combo',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Recipe model."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author',
    )
    name = models.CharField(max_length=200, verbose_name='name')
    image = models.ImageField('Picture', upload_to='recipes/')
    text = models.TextField('Cooking algorithm')
    pub_date = models.DateTimeField(
        'Publication date', auto_now_add=True, db_index=True
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Cooking Time',
        validators=(MinValueValidator(limit_value=1),),
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ingredients',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Tags'
    )

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name

    def image_display(self):
        """Small image thumbnail for admin zone."""

        return mark_safe(f'<img src="{self.image.url}" width="150" />')

    @property
    def favorited(self):
        """Times the recipe has been favorited propery, cached."""

        favorited = cache.get(f'{self.id}_favorited')
        if favorited is None:
            favorited = Favorite.objects.filter(recipe=self).count()
            cache.set(
                f'{self.id}_favorited',
                favorited,
                settings.FAVORITED_CACHE_SECONDS_TTL,
            )
        return favorited


class RecipeIngredient(models.Model):
    """RecipeIngredient model."""

    recipe = models.ForeignKey(
        Recipe, related_name='recipeingredients', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name='recipeingredients', on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(verbose_name='Ingredient amount')

    class Meta:
        verbose_name = 'Recipe Ingredient'
        verbose_name_plural = 'Recipe Ingredients'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Unique ingredient for a recipe',
            ),
        )

    def __str__(self):
        return (
            f'{self.ingredient.name}, {self.amount} '
            f'{self.ingredient.measurement_unit} for {self.recipe}'
        )


class Favorite(models.Model):
    """Favorite model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Bookmarking user',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Favorited recipe',
    )

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'), name='Unique user-recipe bookmark'
            ),
        )

    def __str__(self):
        return f'{self.user} bookmark on {self.recipe}'


class ShoppingCart(models.Model):
    """Shopping cart model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_carts',
        verbose_name='Shopping cart user',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shop_carts',
        verbose_name='Recipe in shopping cart',
    )

    class Meta:
        verbose_name = 'Shopping cart'
        verbose_name_plural = 'Shopping carts'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='Unique user and recipe in cart',
            ),
        )

    def __str__(self):
        return f'{self.recipe} in {self.user} cart'
