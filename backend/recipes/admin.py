from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Recipe, Tag, Ingredient


admin.site.unregister(Group)

@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_display_links = ('name',)
    # list_editable = ('name', )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'times_bookmarked')
    list_display_links = ('title', )
    # autocomplete_fields = ('tags',)
    # list_editable = ('title', 'author', 'tags')
    list_filter = ('title', 'tags', 'author')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    # autocomplete_fields = ('tag',)
    list_editable = ('measurement_unit', )
    # list_filter = ('title', 'tag', 'author')
