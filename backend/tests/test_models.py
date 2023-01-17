from django.contrib.auth import get_user_model
from django.test import TestCase

from recipes.models import Recipe, Ingredient, Tag, RecipeIngredient

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


class HumanReadableTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ingredient = Ingredient.objects.create(name='Pumpkin')
        cls.tag = Tag.objects.create(name='breakfast')
        cls.user = User.objects.create_user(username='auth')
        cls.recipe = Recipe.objects.create(
            author=cls.user,
            name='Potato gnocchi',
            text='You and me and the devil make three',
            cooking_time=15,
        )
        cls.recipeingredient = RecipeIngredient.objects.create(
            recipe=cls.recipe, ingredient=cls.ingredient, amount=1
        )
        cls.recipe.ingredients.add(cls.ingredient)
        cls.recipe.tags.add(cls.tag)

    def test_models_have_correct_object_names(self):
        """Model returns expected str."""

        expected_str = {
            self.recipe.name: str(self.recipe),
            self.tag.name: str(self.tag),
            f'{self.ingredient.name}, {self.ingredient.measurement_unit}': str(
                self.ingredient
            ),
            self.user.username: str(self.recipe.author.username),
            f'{self.ingredient} for {self.recipe}': str(self.recipeingredient)
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
            'tags': 'Tags'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.recipe._meta.get_field(field).verbose_name,
                    expected_value
                )
