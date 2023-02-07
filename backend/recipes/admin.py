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
    def clean(self):
        super(RecipeInlineFormset, self).clean()
        if all([form.cleaned_data.get('DELETE') for form in self.forms]):
            raise ValidationError('You cannot delete all ingredients!')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    autocomplete_fields = ('ingredient',)
    min_num = 1
    formset = RecipeInlineFormset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('ingredient')

    def has_delete_permission(self, request, obj=None):
        return obj.ingredients.count() > 1


class TagInline(admin.TabularInline):
    model = Recipe.tags.through
    min_num = 1
    extra = 0


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'colour', 'slug')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def colour(self, obj):
        return format_html(
            f'<span style="color: {obj.color};">{obj.color}</span>'
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
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
        return [tag.name for tag in obj.tags.all()]

    def times_favorited(self, obj):
        return obj.favorited

    def get_fields(self, request, obj=None, **kwargs):
        """Moves times_favorited to the first place."""

        fields = super().get_fields(request, obj, **kwargs)
        return [fields[-1]] + fields[:-1]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('tags')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = (Lower('name'),)
    list_filter = ('measurement_unit',)
    list_per_page = 200
    list_max_show_all = 5000


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('recipe', 'user')
