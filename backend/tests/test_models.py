from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class CustomUserTests(TestCase):
    """Tests if CustomUser model works as intented."""

    def test_create_user(self):
        """Tests non-admin user creation."""

        user = User.objects.create_user(
            username='Nekrasov',
            email='Nekrasov@yandex.ru',
            password='classic_password',
        )
        self.assertEqual(user.username, 'Nekrasov')
        self.assertEqual(user.email, 'Nekrasov@yandex.ru')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Tests superuser creation."""

        admin_user = User.objects.create_superuser(
            username='dostoevsky',
            email='dost_1821@rambler.ru',
            password='esliboganettovsedozvoleno',
        )
        self.assertEqual(admin_user.username, 'dostoevsky')
        self.assertEqual(admin_user.email, 'dost_1821@rambler.ru')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_long_firstname(self):
        """Tests if longer first names work upon user creation."""

        long_firstname = (
            'Blaine Charles David Earl Frederick Gerald Hubert'
            'Irvin John Kenneth Lloyd Martin Nero Oliver Paul'
            'Sherman Thomas Uncas Victor William Xerxes Yancy Zeus'
        )
        user = User.objects.create_user(
            username='Long',
            email='my_real_name@gmail.com',
            first_name=long_firstname,
        )
        self.assertEqual(user.first_name, long_firstname)


class TestPresets(TestCase):
    """Class with set up data to be inherited from."""

    @classmethod
    def setUpTestData(cls):
        cls.ingredient = Ingredient.objects.create(name='Pumpkin')
        cls.tag = Tag.objects.create(name='breakfast')
        cls.user = User.objects.create_user(
            username='user1', email='user1@gmail.com'
        )
        cls.user2 = User.objects.create_user(
            username='user2', email='user2@gmail.com'
        )
        cls.recipe = Recipe.objects.create(
            author=cls.user,
            name='Potato gnocchi',
            text='You and me and the devil make three',
            cooking_time=15,
            image='test.jpg',
        )
        cls.recipeingredient = RecipeIngredient.objects.create(
            recipe=cls.recipe, ingredient=cls.ingredient, amount=1
        )
        cls.recipe.ingredients.add(cls.ingredient)
        cls.recipe.tags.add(cls.tag)


class HumanReadableTest(TestPresets):
    def test_models_have_correct_object_names(self):
        """Models return expected str."""

        expected_str = {
            self.recipe.name: str(self.recipe),
            self.tag.name: str(self.tag),
            f'{self.ingredient.name}, {self.ingredient.measurement_unit}': str(
                self.ingredient
            ),
            self.user.username: str(self.recipe.author.username),
            (
                f'{self.recipeingredient.ingredient.name}, '
                f'{self.recipeingredient.amount} '
                f'{self.recipeingredient.ingredient.measurement_unit} '
                f'for {self.recipe}'
            ): str(self.recipeingredient),
        }
        for expectation, string in expected_str.items():
            with self.subTest(expectation=expectation):
                self.assertEqual(expectation, string)

    def test_verbose_name(self):
        """Human-readable field verbose names."""

        field_verboses = {
            'author': 'Author',
            'name': 'name',
            'image': 'Picture',
            'text': 'Cooking algorithm',
            'ingredients': 'Ingredients',
            'cooking_time': 'Cooking Time',
            'tags': 'Tags',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.recipe._meta.get_field(field).verbose_name,
                    expected_value,
                )


class ModelValidationTests(TestPresets):
    """Are the validators in models working?"""

    def test_min_cookingtime(self):
        """As per redoc task, cooking time >= 1."""

        self.recipe.full_clean()
        self.recipe.cooking_time = 0
        self.recipe.save()
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_self_subscription(self):
        """Self subscription constraint on the models level."""

        Subscription.objects.create(user=self.user, author=self.user2)
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(user=self.user, author=self.user)

    def test_models_uniquenes(self):
        """Checks unique constraints.
        1. A Recipe can be added to favorites only once.
        2. It can be bookmarked only once.
        3. Only one user-author subscription can be made.
        4. Only unique recipe-ingridient entries can be made."""

        fav = Favorite.objects.count()
        cart = ShoppingCart.objects.count()
        sub = Subscription.objects.count()
        self.assertEqual(RecipeIngredient.objects.count(), 1)
        Favorite.objects.create(recipe=self.recipe, user=self.user)
        ShoppingCart.objects.create(recipe=self.recipe, user=self.user)
        Subscription.objects.create(user=self.user, author=self.user2)
        self.assertEqual(Favorite.objects.count(), fav + 1)
        self.assertEqual(ShoppingCart.objects.count(), cart + 1)
        self.assertEqual(Subscription.objects.count(), sub + 1)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(recipe=self.recipe, user=self.user)
            ShoppingCart.objects.create(recipe=self.recipe, user=self.user)
            Subscription.objects.create(user=self.user, author=self.user2)
            RecipeIngredient.objects.create(
                recipe=self.recipe, ingredient=self.ingredient, amount=10
            )


class CustomFunctionsTests(TestPresets):
    """Do custom models functions work as intented?"""

    def test_favorited(self):
        """Checks if Recipe.favorited works."""

        self.assertEqual(self.recipe.favorited, 0)
        favorite = Favorite.objects.create(recipe=self.recipe, user=self.user)
        self.assertEqual(self.recipe.favorited, 1)
        favorite.delete()
        self.assertEqual(self.recipe.favorited, 0)
