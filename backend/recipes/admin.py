from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.forms import BaseInlineFormSet, CheckboxSelectMultiple
from django.utils.html import format_html

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

admin.site.unregister(Group)


class RecipeInlineFormset(BaseInlineFormSet):
    """Formset to prevent all ingrediets deletion."""

    def clean(self):
        if all([form.cleaned_data.get('DELETE') for form in self.forms]):
            raise ValidationError('You cannot delete all ingredients!')
        super().clean()


class RecipeIngredientInline(admin.TabularInline):
    """Inline for recipe ingredients."""

    model = RecipeIngredient
    extra = 0
    autocomplete_fields = ('ingredient',)
    min_num = 1
    formset = RecipeInlineFormset

    def get_queryset(self, request):
        """Select_related to optimize db usage."""

        qs = super().get_queryset(request)
        return qs.select_related('ingredient', 'recipe')

    def has_delete_permission(self, request, obj=None):
        """No deletion checkbox if there's only 1 recipe ingredient left."""

        return obj.ingredients.count() > 1


class TagInline(admin.TabularInline):
    """Inline for tags."""

    model = Recipe.tags.through
    min_num = 1
    extra = 0

    def get_queryset(self, request):
        """Prefetch recipes for optimized db queries."""

        qs = super().get_queryset(request)
        return qs.prefetch_related('recipes')


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    """Tags admin interface."""

    list_display = ('name', 'colour', 'slug')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def colour(self, obj):
        """Colored color codes for fun."""

        return format_html(
            f'<span style="color: {obj.color};">{obj.color}</span>'
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for recipes."""

    readonly_fields = ('times_favorited',)
    list_display = (
        'name',
        'author',
        'recipe_tags',
        'image_display',
    )
    list_filter = ('name', 'tags', 'author')
    inlines = (RecipeIngredientInline,)
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    def recipe_tags(self, obj):
        """Recipes tags for recipe list."""

        return [tag.name for tag in obj.tags.all()]

    def times_favorited(self, obj):
        """Times favorited field for recipe list."""

        return obj.favorited

    def get_fields(self, request, obj=None, **kwargs):
        """Moves times_favorited to the first place."""

        fields = super().get_fields(request, obj, **kwargs)
        return [fields[-1]] + fields[:-1]

    def get_queryset(self, request):
        """Prefetching related to optimize db usage."""

        qs = super().get_queryset(request)
        return qs.prefetch_related('tags', 'ingredients')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin interface for ingredients."""

    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = (Lower('name'),)
    list_filter = ('measurement_unit',)
    list_per_page = 200
    list_max_show_all = 5000


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin interface for favorites."""

    list_display = ('user', 'recipe')
    list_select_related = True


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin interface for the shopping cart."""

    list_display = ('user', 'recipe')

    def get_queryset(self, request):
        """Queries optimization."""

        qs = super().get_queryset(request)
        return qs.select_related('recipe', 'user')
