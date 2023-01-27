from django.contrib.auth import get_user_model
from django.test import TestCase

from api.utils import get_grocery_list
from recipes.models import Ingredient, Recipe, RecipeIngredient, ShoppingCart

User = get_user_model()


class TestShoppingList(TestCase):
    """Set of tests to check if the shopping list util behaves correctly."""

    @classmethod
    def setUpTestData(cls):
        cls.ingredient1 = Ingredient.objects.create(
            name='Pumpkin', measurement_unit='ea'
        )
        cls.ingredient2 = Ingredient.objects.create(
            name='Chicken', measurement_unit='g.'
        )
        cls.ingredient3 = Ingredient.objects.create(
            name='Salt', measurement_unit='to taste'
        )
        cls.user = User.objects.create_user(
            username='cook', email='e1@mail.com'
        )
        cls.user2 = User.objects.create_user(
            username='amateur', email='e2@mail.com'
        )
        presets = {
            'cooking_time': 15,
            'author': cls.user,
        }
        cls.recipe1 = Recipe.objects.create(**presets, name='1')
        cls.recipe2 = Recipe.objects.create(**presets, name='2')
        cls.recipe3 = Recipe.objects.create(**presets, name='3')

        RecipeIngredient.objects.create(
            recipe=cls.recipe1, ingredient=cls.ingredient1, amount=100
        )
        RecipeIngredient.objects.create(
            recipe=cls.recipe1, ingredient=cls.ingredient2, amount=100
        )
        RecipeIngredient.objects.create(
            recipe=cls.recipe2, ingredient=cls.ingredient2, amount=100
        )
        RecipeIngredient.objects.create(
            recipe=cls.recipe3, ingredient=cls.ingredient3, amount=10
        )

        cls.recipe1.ingredients.add(cls.ingredient1)
        cls.recipe1.ingredients.add(cls.ingredient2)
        cls.recipe2.ingredients.add(cls.ingredient2)
        cls.recipe3.ingredients.add(cls.ingredient3)
        ShoppingCart.objects.create(user=cls.user, recipe=cls.recipe1)
        ShoppingCart.objects.create(user=cls.user, recipe=cls.recipe2)

    def test_grocery_dictionary(self):
        """Do items from shopping cart exist in correct amounts?
        Are items not from the shopping cart missing?"""

        result = get_grocery_list(self.user)
        self.assertIn(('Chicken', 'g.'), result)
        self.assertIn(('Pumpkin', 'ea'), result)
        self.assertNotIn(('Salt', 'to taste'), result)
        self.assertEqual(result[('Chicken', 'g.')], 200)
        self.assertEqual(result[('Pumpkin', 'ea')], 100)

    def test_empty_grocery_list(self):
        """Check for empty dictionary if there're not recipes in list."""

        result = get_grocery_list(self.user2)
        self.assertIsInstance(result, dict)
        self.assertDictEqual(result, {})
