import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, override_settings

from api.urls import router
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def generate_recipe(author):
    """Generate and create a recipe by author."""

    fake = Faker()
    return Recipe.objects.create(
        author=author,
        text=fake.text(),
        name=fake.sentence(),
        cooking_time=fake.pyint(),
        image=fake.file_path(depth=3, category='image'),
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AuthorizedUserAuthorPresets(APITestCase):
    """Preset for the following classes to inherit."""

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(**cls.user_details)
        cls.author = User.objects.create_user(**cls.author_details)
        cls.user_client, cls.author_client = APIClient(), APIClient()
        cls.user_client.force_authenticate(cls.user)
        cls.author_client.force_authenticate(cls.author)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UnauthorizedUserTests(APITestCase):
    """Unauthorized users cannot access some pages."""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        cls.author = User.objects.create(
            email='testuser@user.com', username='Tester'
        )
        cls.recipe = generate_recipe(cls.author)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_endpoints_without_tokens(self):
        """No token requests return correct status codes."""

        get_endpoints = (
            reverse('users-me'),
            reverse('users-subscriptions'),
            reverse('users-subscribe', kwargs={'pk': self.author.id}),
        )
        post_endpoints = (
            reverse('users-set-password'),
            reverse('recipes-favorite', kwargs={'pk': self.recipe.id}),
            reverse('users-subscribe', kwargs={'pk': self.author.id}),
            reverse('recipes-list'),
            reverse('recipes-detail', kwargs={'pk': self.recipe.id})
            + 'shopping_cart/',
        )
        for endpoint in get_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    self.client.get(endpoint).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )
        for endpoint in post_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    self.client.post(endpoint, {}, format='json').status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_user_registration(self):
        """Tests if user registration endpoint works as expected."""

        payload = {
            'email': 'gonna_test@email.com',
            'username': 'ThisIsMyVillage',
            'password': 'SuchANicevillage',
            'first_name': 'Gadiukino',
        }
        response = self.client.post(
            reverse('users-list'), payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload['last_name'] = 'Raiders'
        response = self.client.post(
            reverse('users-list'), payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 5)
        for field in 'email', 'username', 'first_name', 'last_name':
            with self.subTest(field=field):
                self.assertEqual(payload[field], response.data[field])
        self.assertIn('id', response.data)
        new_user = User.objects.last()
        for field in 'email', 'username', 'first_name', 'last_name', 'id':
            with self.subTest(field=field):
                self.assertEqual(
                    response.data[field], getattr(new_user, field)
                )
        self.assertTrue(new_user.check_password(payload['password']))


class AuthsEndpointsTests(APITestCase):
    """Tests for auth endpoints."""

    def test_get_token_and_logout(self):
        """Check if we can obtain a working token, and we can delete it."""

        data = {
            'email': 'hello@space.com',
            'password': 'testPassword',
        }
        user = User.objects.create(email=data['email'])
        user.set_password(data['password'])
        user.save()
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)
        self.assertEqual(len(response.data), 1)
        token = response.data['auth_token']
        self.assertIsNotNone(token)
        logout_url = reverse('logout')
        self.assertEqual(
            self.client.post(logout_url, {}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self.assertEqual(
            self.client.post(logout_url, {}).status_code,
            status.HTTP_204_NO_CONTENT,
        )


class SubscriptionEndpointsTests(AuthorizedUserAuthorPresets):
    """Tests for auth endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.user_details = {
            'username': 's_user',
            'email': 's_u@i.com',
            'first_name': 'William',
            'last_name': 'Tell',
            'password': 'WhoWillTell',
        }
        cls.author_details = {
            'username': 's_author',
            'email': 's_author@mail.com',
            'last_name': 'S_Auth',
            'first_name': 'I_Me_Mine',
            'password': 'Walrus',
        }
        cls.fake = Faker()
        super().setUpClass()
        cls.recipe = generate_recipe(cls.author)
        cls.recipes = [generate_recipe(author=cls.author) for _ in range(10)]

    def test_subscriptions_endpoint(self):
        """Tests functionality of subscription endpoint."""

        prev_subs = Subscription.objects.count()
        subscribe_url = reverse(
            'users-subscribe', kwargs={'pk': self.author.id}
        )
        subscriptions_url = reverse('users-subscriptions')
        response = self.user_client.get(subscriptions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author_ids = []
        for author in response.data['results']:
            author_ids.append(author['id'])
        self.assertNotIn(self.author.id, author_ids)
        response = self.user_client.post(subscribe_url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.user_client.post(subscribe_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Subscription.objects.count(), prev_subs + 1)
        last_subscription = Subscription.objects.last()
        self.assertEqual(last_subscription.user, self.user)
        self.assertEqual(last_subscription.author, self.author)
        response = self.user_client.get(subscriptions_url)
        author_ids = []
        for author in response.data['results']:
            author_ids.append(author['id'])
        self.assertIn(self.author.id, author_ids)
        response = self.user_client.delete(subscribe_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subscription.objects.count(), prev_subs)
        response = self.user_client.get(subscriptions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        author_ids = []
        for author in response.data['results']:
            author_ids.append(author['id'])
        self.assertNotIn(self.author.id, author_ids)

    def test_subscriptions_fields(self):
        """Tests that subscriptions fields are correct."""

        subscribe_url = reverse(
            'users-subscribe', kwargs={'pk': self.author.id}
        )
        response = self.user_client.post(subscribe_url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 8)
        for field in 'id', 'email', 'username', 'first_name', 'last_name':
            with self.subTest(field=field):
                self.assertEqual(
                    response.data[field], getattr(self.author, field)
                )
        self.assertTrue(response.data['is_subscribed'])
        self.assertEqual(
            response.data['recipes_count'], self.author.recipes.count()
        )
        self.assertEqual(len(response.data['recipes']), 5)
        self.assertEqual(len(response.data['recipes'][0]), 4)
        first_recipe = response.data['recipes'][0]
        recipe = Recipe.objects.get(id=first_recipe['id'])
        self.assertEqual(recipe.name, first_recipe['name'])
        self.assertEqual(recipe.cooking_time, first_recipe['cooking_time'])
        self.assertTrue(first_recipe['image'].endswith(recipe.image.url))

    def test_nested_recipes_limit_in_subscriptions(self):
        """Tests if recipes_limit argument works as intended."""

        url = reverse('users-subscribe', kwargs={'pk': self.author.id})
        response = self.user_client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['recipes']), 5)
        Subscription.objects.last().delete()
        url = reverse('users-subscribe', kwargs={'pk': self.author.id})
        response = self.user_client.post(url + '?recipes_limit=3', {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['recipes']), 3)
        url = reverse('users-subscriptions')
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'][0]['recipes']), 5)
        response = self.user_client.get(url + '?recipes_limit=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'][0]['recipes']), 3)

    def test_users_list_subscription_status(self):
        """Tests if subscriptions display correctly in users list."""

        user2 = User.objects.create(
            username='BadAuthor',
            email='dont@subscribeto.me',
            first_name='Julia',
            last_name='Visotskaya',
            password='SmeshatMaslo',
        )
        user_id, author_id, bad_author_id = (
            self.user.id,
            self.author.id,
            user2.id,
        )
        url = reverse('users-list') + f'?limit={User.objects.count()}'
        response = self.user_client.get(url)
        subscriptions = {
            user['id']: user['is_subscribed']
            for user in response.data['results']
        }
        for field in user_id, author_id, bad_author_id:
            with self.subTest(field=field):
                self.assertFalse(subscriptions[field])
        Subscription.objects.create(user=self.user, author=self.author)
        response = self.user_client.get(url)
        subscriptions = {
            user['id']: user['is_subscribed']
            for user in response.data['results']
        }
        for field in user_id, bad_author_id:
            with self.subTest(field=field):
                self.assertFalse(subscriptions[field])
        self.assertTrue(subscriptions[author_id])


class UsersEndpointTests(AuthorizedUserAuthorPresets):
    """Tests for users endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.user_details = {
            'username': 'user',
            'email': 'user@i.com',
            'first_name': 'William',
            'last_name': 'Tell',
            'password': 'WhoWillWin',
        }
        cls.author_details = {
            'username': 'author',
            'email': 'author@mail.com',
            'first_name': 'Alexander',
            'last_name': 'The Great',
            'password': 'DontConquer',
        }
        super().setUpClass()

    def test_create_user(self):
        """Create a user, check response codes and fields."""

        payload = {
            'email': 'hodleo2@ngfs.com',
            'username': 'Willie',
            'first_name': '',
            'last_name': 'Wonka',
            'password': 'Qwerffty123Qwerty123',
        }
        response = self.client.post(reverse('users-list'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload['first_name'] = 'Willy'
        response = self.client.post(reverse('users-list'), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(len(response.data), 5)
        self.assertNotIn('is_subscribed', data)
        payload['id'] = User.objects.last().id
        for field in data.keys():
            with self.subTest(field=field):
                self.assertEqual(payload[field], data[field])

    def test_user_list(self):
        """Tests for users list."""

        user = User.objects.create(
            email='hello@space.com',
            username='enjoykin',
            first_name='Garazh',
            last_name='Nash',
            password='shokolad',
        )
        response = self.client.get(reverse('users-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['results'][0]
        self.assertEqual(len(user_data), 6)
        for field in (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        ):
            with self.subTest(field=field):
                self.assertIn(field, user_data)
        self.assertFalse(user_data['is_subscribed'])

    def test_user_profile(self):
        """Existing user is visible to others."""

        user = User.objects.create(email='hello@kitty.com')
        url = reverse('users-detail', kwargs={'pk': 100500})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        url = reverse('users-detail', kwargs={'pk': user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'hello@kitty.com')
        self.assertEqual(len(response.data), 6)
        for field in (
            'email',
            'username',
            'id',
            'first_name',
            'last_name',
            'is_subscribed',
        ):
            with self.subTest(field=field):
                self.assertIn(field, response.data)

    def test_subscriptions_on_users_page(self):
        """Create a subscription, check that it shows on /users/ endpoint."""

        Subscription.objects.create(user=self.user, author=self.author)
        url = reverse('users-list')
        user_results = self.user_client.get(url).data['results']
        author_results = self.author_client.get(url).data['results']
        for result in user_results:
            if result['id'] == self.author.id:
                self.assertTrue(result['is_subscribed'])
        for result in author_results:
            if result['id'] == self.user.id:
                self.assertFalse(result['is_subscribed'])

    def test_my_profile(self):
        """Test if the user profile is correct."""

        response = self.user_client.get(reverse('users-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_details = self.user_details
        user_details.pop('password')
        for field in user_details.keys():
            with self.subTest(field=field):
                self.assertEqual(
                    response.data[field], self.user_details[field]
                )
        self.assertIn('id', response.data)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertIn('is_subscribed', response.data)
        self.assertFalse(response.data['is_subscribed'])

    def test_password_change(self):
        """Check if valid password change changes the password."""

        url = reverse('users-set-password')
        creds = {'current_password': 'even_this', 'new_password': '111'}
        self.user.set_password(creds['current_password'])
        self.user.save()
        self.assertTrue(self.user.check_password(creds['current_password']))
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 400)
        creds['new_password'] = 'me'
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 400)
        creds['new_password'] = 'on_a_second_thought'
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, None)
        self.assertTrue(self.user.check_password(creds['new_password']))


class ShoppingCardEndpointsTests(APITestCase):
    """Tests for shopping cart endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.author = User.objects.create_user(
            username='shopper',
            email='cart_tester@yandex.com',
            password='shopwithme',
            first_name='checkme',
            last_name='cmon',
        )
        cls.author_client = APIClient()
        cls.author_client.force_authenticate(cls.author)
        super().setUpClass()

    def test_shoppingcart_endpoint(self):
        """Check if post/delete work correctly."""

        recipe = generate_recipe(author=self.author)
        url = (
            reverse('recipes-detail', kwargs={'pk': recipe.id})
            + 'shopping_cart/'
        )
        carts_amount = ShoppingCart.objects.count()
        response = self.author_client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ShoppingCart.objects.count(), carts_amount + 1)
        self.assertEqual(
            ShoppingCart.objects.get(recipe=recipe, user=self.author),
            ShoppingCart.objects.last(),
        )
        self.assertEqual(len(response.data), 4)
        for field in 'id', 'name', 'image', 'cooking_time':
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        response = self.author_client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.author_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.author_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_shopping_cart_pdf_download(self):
        """Tests if the PDF download endpoint works as intended."""

        recipe = generate_recipe(self.author)
        ShoppingCart.objects.create(recipe=recipe, user=self.author)
        ingredient = Ingredient.objects.create(
            name='ladybugs', measurement_unit='ea'
        )
        RecipeIngredient.objects.create(
            amount=10, ingredient=ingredient, recipe=recipe
        )
        response = self.author_client.get(
            reverse('recipes-download-shopping-cart')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/pdf')
        self.assertGreaterEqual(len(response.content), 1000)


class IngredientEndpointsTests(APITestCase):
    """Tests for ingredients endpoins."""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        super().setUpClass()

    def test_ingredients(self):
        """Test ingredients endpoint."""

        names = self.fake.words(10, unique=True)
        ingredients = [
            Ingredient.objects.create(
                name=name, measurement_unit=self.fake.word()
            )
            for name in names
        ]

        response = self.client.get(
            reverse('ingredients-detail', kwargs={'pk': ingredients[0].id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        for field in 'measurement_unit', 'id', 'name':
            with self.subTest(field=field):
                self.assertEqual(
                    response.data[field], getattr(ingredients[0], field)
                )

        response = self.client.get(reverse('ingredients-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(names))
        response = self.client.get(
            reverse('ingredients-detail', kwargs={'pk': 100})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ingredients_search(self):
        """Tests if search behaves as expected and puts startswith first."""

        objects = [
            Ingredient(name='Banana', measurement_unit='kilo'),
            Ingredient(name='avocado', measurement_unit='ea'),
            Ingredient(name='burrito', measurement_unit='kilo'),
        ]
        Ingredient.objects.bulk_create(objects)
        response = self.client.get(reverse('ingredients-list') + '?name=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'avocado')
        self.assertEqual(response.data[1]['name'], 'Banana')
        response = self.client.get(reverse('ingredients-list'))
        self.assertEqual(len(response.data), 3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RecipesEndpointsTests(APITestCase):
    """Tests for ingredients endpoins."""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        cls.fields = {
            'tags': list,
            'ingredients': list,
            'id': int,
            'cooking_time': int,
            'author': dict,
            'is_favorited': bool,
            'is_in_shopping_cart': bool,
            'image': str,
            'name': str,
            'text': str,
        }
        cls.author = User.objects.create(
            email='recipe@cooking.org', username='ChefMing'
        )
        cls.user = User.objects.create(
            email='angrydave@reddit.com', username='AngryDave'
        )
        cls.author_client, cls.user_client = APIClient(), APIClient()
        cls.author_client.force_authenticate(cls.author)
        cls.user_client.force_authenticate(cls.user)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_recipes_list(self):
        """Recipes list has all the necessary fields in correct formats."""

        response = self.client.get(reverse('recipes-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'][0]
        self.assertEqual(len(data), 10)
        for field in self.fields.keys():
            with self.subTest(field=field):
                self.assertIn(field, data)
        for field, inst in self.fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(data[field], inst)
        self.assertTrue(
            response.data['results'][0]['image'].startswith('http://')
        )

    def test_recipe_detail_fields(self):
        """Are the returned fields in recipe details correct."""

        recipe = generate_recipe(author=self.author)
        response = self.client.get(
            reverse('recipes-detail', kwargs={'pk': recipe.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        for field in self.fields.keys():
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        for field, inst in self.fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(response.data[field], inst)
        for field in ('id', 'name', 'text', 'cooking_time'):
            with self.subTest(field=field):
                self.assertEqual(getattr(recipe, field), response.data[field])
        self.assertFalse(response.data['is_favorited'])
        self.assertFalse(response.data['is_in_shopping_cart'])
        self.assertTrue(response.data['image'].endswith(recipe.image.url))

    def test_create_recipe(self):
        """Tests recipe creation and response."""

        prev_recipes = Recipe.objects.count()
        url = reverse('recipes-list')
        names = self.fake.words(3, unique=True)
        tags = [
            Tag.objects.create(
                name=name, color=self.fake.color().upper(), slug=name
            )
            for name in names
        ]
        words = self.fake.words(3, unique=True)
        ingredients = [
            Ingredient.objects.create(
                name=word, measurement_unit=self.fake.word()
            )
            for word in words
        ]
        recipe_presets = {
            'ingredients': [
                {'id': ingredient.id, 'amount': self.fake.pyint()}
                for ingredient in ingredients
            ],
            'tags': [],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII=',
            'name': self.fake.sentence(),
            'text': self.fake.sentence(),
            'cooking_time': self.fake.pyint(),
        }
        response = self.author_client.post(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        recipe_presets['tags'] = [1000, 2000]
        response = self.author_client.post(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        recipe_presets['tags'] = [tag.id for tag in tags]
        response = self.author_client.post(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), prev_recipes + 1)
        self.assertEqual(len(response.data), 10)
        for field in self.fields.keys():
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        for field, inst in self.fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(response.data[field], inst)
        url = reverse('recipes-detail', kwargs={'pk': response.data['id']})
        response = self.author_client.put(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.user_client.delete(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recipe_list_filters(self):
        """Are the filters working correctly?"""

        tags = [
            Tag.objects.create(name=slug, slug=slug, color=slug)
            for slug in ('red', 'green', 'blue')
        ]
        recipes = [generate_recipe(self.author) for _ in range(3)]
        recipes[0].tags.set([tags[0], tags[1]])
        recipes[1].tags.set([tags[1], tags[2]])
        recipes[2].tags.set([tags[2], tags[0]])
        Favorite.objects.create(user=self.user, recipe=recipes[0])
        ShoppingCart.objects.create(user=self.user, recipe=recipes[1])
        response = self.user_client.get(reverse('recipes-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for i in range(len(recipes)):
            with self.subTest(i=i):
                self.assertEqual(
                    recipes[i].id, response.data['results'][2 - i]['id']
                )
        response = self.user_client.get(
            reverse('recipes-list') + '?tags=green'
        )
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(
            response.data['results'][0]['tags'][0]['slug'], tags[1].slug
        )
        self.assertEqual(
            response.data['results'][1]['tags'][1]['slug'], tags[1].slug
        )
        response = self.user_client.get(
            reverse('recipes-list') + '?is_favorited=1'
        )
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['author']['id'], self.author.id
        )
        response = self.user_client.get(
            reverse('recipes-list') + '?is_in_shopping_cart=1'
        )
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['is_in_shopping_cart'], True
        )

    def test_recipes_update(self):
        """Test if update works correctly."""

        tags = [
            Tag.objects.create(name=slug, slug=slug, color=slug)
            for slug in ('red', 'green', 'blue')
        ]
        ingredients = [
            Ingredient.objects.create(name=name, measurement_unit=m_unit)
            for name, m_unit in {'Carrots': 'g.', 'Water': 'oz'}.items()
        ]
        recipe = generate_recipe(self.author)
        recipe.tags.set([tags[0], tags[1]])
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=ingredients[0], amount=10
        )

        payload = {
            'tags': [tags[1].id, tags[2].id],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII=',
            'name': 'test_update_name',
            'text': 'test_update_text',
            'cooking_time': 10,
            'ingredients': [dict(id=ingredients[1].id, amount=-1)],
        }
        url = reverse('recipes-detail', kwargs={'pk': recipe.id})
        response = self.user_client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.author_client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload['ingredients'] = [dict(id=ingredients[1].id, amount=5)]
        response = self.author_client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data['tags']), 2)
        self.assertEqual(len(data['ingredients']), 1)
        self.assertEqual(data['name'], 'test_update_name')
        recipe.refresh_from_db()
        for field in 'cooking_time', 'text', 'name':
            with self.subTest(field=field):
                self.assertEqual(getattr(recipe, field), payload[field])
        self.assertEqual(
            RecipeIngredient.objects.get(
                recipe=recipe, ingredient=ingredients[1]
            ).amount,
            5,
        )
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tags[1], recipe.tags.all())
        self.assertIn(tags[2], recipe.tags.all())
        self.assertIn(ingredients[1], recipe.ingredients.all())
        self.assertFalse(recipe.image.url.endswith('1.jpg'))

    def test_delete_recipe(self):
        """Tests if recipe deletion works as intended."""

        recipe = generate_recipe(self.author)
        url = reverse('recipes-detail', kwargs={'pk': recipe.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.user_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        recipes_amount = Recipe.objects.count()
        response = self.author_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.count(), recipes_amount - 1)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)
        response = self.author_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FavoriteEndpointsTests(APITestCase):
    """Tests for favorite endpoins."""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        cls.author = User.objects.create(
            email='favorite@food.com', username='JuliaCh'
        )
        cls.user = User.objects.create(email='amused@to.d', username='Bill')
        cls.user_client = APIClient()
        cls.user_client.force_authenticate(cls.user)
        cls.recipe = generate_recipe(cls.author)
        super().setUpClass()

    def test_favorite_endpoint(self):
        """Tests for favorite endpoint."""

        Favorite.objects.create(user=self.author, recipe=self.recipe)
        previous_favs = Favorite.objects.count()
        url = reverse('recipes-favorite', kwargs={'pk': self.recipe.id})
        response = self.user_client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), previous_favs + 1)
        self.assertEqual(len(response.data), 4)
        for field in 'id', 'name', 'image', 'cooking_time':
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['cooking_time'], int)
        self.assertIsInstance(response.data['image'], str)
        self.assertIsInstance(response.data['name'], str)
        self.assertEqual(response.data['id'], self.recipe.id)
        self.assertEqual(response.data['name'], self.recipe.name)
        self.assertEqual(
            response.data['cooking_time'], self.recipe.cooking_time
        )
        self.assertIn('://', response.data['image'])
        response = self.user_client.post(url, {})
        self.assertEqual(response.status_code, 400)
        response = self.user_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), previous_favs)


class TagsEndpointsTests(APITestCase):
    """Tests for favorite endpoins."""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        cls.names = cls.fake.words(10, unique=True)
        cls.tags = [
            Tag.objects.create(
                name=name, color=cls.fake.color().upper(), slug=name
            )
            for name in cls.names
        ]
        super().setUpClass()

    def test_tags(self):
        """Test tags endpoint."""

        response = self.client.get(
            reverse('tags-detail', kwargs={'pk': self.tags[0].id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        for field in 'color', 'id', 'name', 'slug':
            with self.subTest(field=field):
                self.assertEqual(
                    response.data[field], getattr(self.tags[0], field)
                )

        response = self.client.get(reverse('tags-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.names))
        response = self.client.get(reverse('tags-detail', kwargs={'pk': 100}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PaginationTests(APITestCase):
    """ "Are the pagination arguments and fields named correctly?"""

    @classmethod
    def setUpClass(cls):
        cls.fake = Faker()
        usernames = cls.fake.words(11, unique=True)
        cls.users = [
            User.objects.create(
                username=username,
                email=username + '.' + cls.fake.email(),
                first_name=cls.fake.first_name(),
                last_name=cls.fake.last_name(),
                password=cls.fake.password(),
            )
            for username in usernames[:10]
        ]
        cls.subscriber = User.objects.create(username=usernames[-1])
        cls.subscriptions = [
            Subscription.objects.create(user=cls.subscriber, author=user)
            for user in cls.users
        ]
        cls.subscriber_client = APIClient()
        cls.subscriber_client.force_authenticate(cls.subscriber)
        cls.recipes = [generate_recipe(cls.subscriber) for _ in range(10)]
        cls.paginated_pages = {
            reverse('users-list'): User.objects.count(),
            reverse('users-subscriptions'): Subscription.objects.count(),
            reverse('recipes-list'): Recipe.objects.count(),
        }
        super().setUpClass()

    def test_paginated_pages(self):
        """Tests that the pagination is on and uses correct kwargs."""

        for url, amount in self.paginated_pages.items():
            response = self.subscriber_client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for field in 'count', 'next', 'previous', 'results':
                with self.subTest(field=field):
                    self.assertIn(field, response.data)
            self.assertEqual(len(response.data), 4)
            response = self.subscriber_client.get(url, {'limit': 3, 'page': 3})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['count'], amount)
            self.assertTrue(response.data['next'].endswith('?limit=3&page=4'))
            self.assertTrue(
                response.data['previous'].endswith('?limit=3&page=2')
            )


class URLTests(APITestCase):
    """Tests for project urls."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.router_urls = {
            'users-list': '/api/users/',
            'users-me': '/api/users/me/',
            'users-subscriptions': '/api/users/subscriptions/',
            'users-set-password': '/api/users/set_password/',
            'tags-list': '/api/tags/',
            'ingredients-list': '/api/ingredients/',
            'recipes-list': '/api/recipes/',
            'api-root': '/api/',
            'recipes-download-shopping-cart': '/api/recipes/download_shopping_cart/',
        }
        cls.router_detailed_urls = {
            'tags-detail': '/api/tags/1/',
            'ingredients-detail': '/api/ingredients/1/',
            'recipes-detail': '/api/recipes/1/',
            'recipes-shopping-cart': '/api/recipes/1/shopping_cart/',
            # 'recipes-favorite': '/api/recipes/1/favorite/',
        }
        cls.auth_urls = {
            'login': '/api/auth/token/login',
            'logout': '/api/auth/token/logout',
        }
        cls.users_urls = {
            'users-subscribe': '/api/users/1/subscribe/',
            'users-detail': '/api/users/1/',
        }
        return super().setUpClass()

    def test_djoser_filtered(self):
        """Tests if djosers urls are sucessfully filtered out."""

        filtered_urls = set(url.name for url in router.get_urls())
        for endpoint_name in (
            'users-resend-activation',
            'users-reset-password',
            'users-reset-password-confirm',
            'users-reset-username',
            'users-reset-username-confirm',
            'users-set-username',
        ):
            with self.subTest(endpoint_name=endpoint_name):
                self.assertNotIn(endpoint_name, filtered_urls)
        for endpoint_name in self.router_urls.keys():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertIn(endpoint_name, filtered_urls)
        for endpoint_name in self.router_detailed_urls.keys():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertIn(endpoint_name, filtered_urls)

    def test_resolved_urls(self):
        """Tests if the resolved urls comply to the specifications."""

        for endpoint_name, url in self.router_urls.items():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertTrue(reverse(endpoint_name).endswith(url))
        for endpoint_name, url in self.auth_urls.items():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertEqual(reverse(endpoint_name), url)
        for endpoint_name, url in self.router_detailed_urls.items():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertTrue(
                    reverse(endpoint_name, kwargs={'pk': 1}).endswith(url)
                )
        for endpoint_name, url in self.users_urls.items():
            with self.subTest(endpoint_name=endpoint_name):
                self.assertTrue(
                    reverse(endpoint_name, kwargs={'pk': 1}).endswith(url)
                )

    def test_custom_404_handler(self):
        """Test if the custom 404 handler is working."""

        response = self.client.get('/api/sghpehvnwinpwneg')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(
            response.json()['error'], 'The resource was not found'
        )
