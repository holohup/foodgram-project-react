from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Recipe, Tag, Ingredient, Favorite, RecipeIngredient


admin.site.unregister(Group)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient', )
    # search_fields = ('ingredients',)


@admin.register(Tag)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_display_links = ('name',)
    # list_editable = ('name', )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'recipe_tags', 'favorited')
    list_filter = ('name', 'tags', 'author')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]

    def recipe_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def favorited(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    # autocomplete_fields = ('tag',)
    list_editable = ('measurement_unit', )
    # list_filter = ('title', 'tag', 'author')
    search_fields = ('name',)
    list_per_page = 200
    list_max_show_all = 5000
