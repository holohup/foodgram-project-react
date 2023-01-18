from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html

from .models import (
    Recipe, Tag, Ingredient, RecipeIngredient, Favorite, ShoppingCart
)

admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
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
    readonly_fields = ('times_favorited',)
    list_display = ('name', 'author', 'recipe_tags', 'favorited')
    list_filter = ('name', 'tags', 'author')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]

    def recipe_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def times_favorited(self, obj):
        return obj.favorited

    def get_fields(self, request, obj=None, **kwargs):
        """Moves times_favorited to the first place."""

        fields = super().get_fields(request, obj, **kwargs)
        return [fields[-1]]+fields[:-1]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('name', )
    list_per_page = 200
    list_max_show_all = 5000


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')

#     def get_queryset(self, request):
#         qs = super().get_queryset(request).order_by('user').distinct('user')
#         return qs.prefetch_related('recipe', 'user')

#     def get_recipes(self, obj):
#         return list(Recipe.objects.filter(shop_cart__user=obj.user))

#     # def get_users(self, obj):
#     #     return CustomUser.objects.filter(shop_cart__user=obj.user)
