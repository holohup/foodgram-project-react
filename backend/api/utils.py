from django.contrib.auth import get_user_model

from recipes.models import Recipe, RecipeIngredient

User = get_user_model()


def get_grocery_list(user: User):
    recipes = Recipe.objects.filter(shop_cart__user=user)
    recipe_ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
    result = {}
    for item in recipe_ingredients:
        key = (item.ingredient.name, item.ingredient.measurement_unit)
        if key not in result:
            result[key] = 0
        result[key] += item.amount
    return result

