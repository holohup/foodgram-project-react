from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html

from .models import (
    Recipe, Tag, Ingredient, Favorite,
    RecipeIngredient, ShoppingCart
)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient', )


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'colored', 'slug')
    list_display_links = ('name',)

    def colored(self, obj):
        return format_html(
            f'<span style="color: {obj.color};">{obj.color}</span>'
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'recipe_tags', 'favorited')
    list_filter = ('name', 'tags', 'author')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]
    # fieldsets = (
    #     (None, {
    #         'fields': ('name', 'author',),
    #     }),
    # )

    def recipe_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def favorited(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    list_editable = ('measurement_unit', )
    search_fields = ('name',)
    list_filter = ('name', )
    list_per_page = 200
    list_max_show_all = 5000


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass
