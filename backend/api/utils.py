import os
from io import BytesIO
from typing import List, NamedTuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import get_template

from recipes.models import Recipe, RecipeIngredient

User = get_user_model()


class ShoppingCartItem(NamedTuple):
    name: str
    measurement_unit: str
    amount: int


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


def plain_data_to_cart_items(data: dict) -> List[ShoppingCartItem]:
    result = []
    for ingredient, amount in data.items():
        result.append(
            ShoppingCartItem(
                name=ingredient[0],
                measurement_unit=ingredient[1],
                amount=amount,
            )
        )
    return result
