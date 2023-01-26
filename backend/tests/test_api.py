# from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscription

User = get_user_model()


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


class UnauthorizedUserTests(APITestCase):
    @classmethod
    def setUp(cls):
        """Tests presets."""

        cls.testuser = User.objects.create(
            username='testuser',
            email='test@test.com',
            password='testpasswordtestpassword',
            first_name='Test',
            last_name='User',
        )
        cls.fake = Faker()
        cls.recipe = Recipe.objects.create(
            author=cls.testuser,
            text=cls.fake.text(),
            name=cls.fake.sentence(),
            cooking_time=cls.fake.pyint(),
            image='/images/test.jpg',
        )

    def test_get_token_and_logout(self):
        """Check if we can obtain a working token, and we can delete it."""

        user = User.objects.create(email='hello@space.com')
        user.set_password('testPassword')
        user.save()
        data = {
            'email': 'hello@space.com',
            'password': 'testPassword',
        }
        response = self.client.post(reverse('get_token'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
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

    def test_user_list(self):
        User.objects.create(email='hello@space.com')
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

    def test_tags(self):
        """Test tags endpoint."""

        names = self.fake.words(10, unique=True)
        tags = [
            Tag.objects.create(
                name=name, color=self.fake.color().upper(), slug=name
            )
            for name in names
        ]

        response = self.client.get(
            reverse('tags-detail', kwargs={'pk': tags[0].id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        for field in 'color', 'id', 'name', 'slug':
            with self.subTest(field=field):
                self.assertEqual(response.data[field], getattr(tags[0], field))

        response = self.client.get(reverse('tags-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(names))
        response = self.client.get(reverse('tags-detail', kwargs={'pk': 100}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
            Ingredient(name='burrito', measurement_unit='kilo')
        ]
        Ingredient.objects.bulk_create(objects)
        response = self.client.get(reverse('ingredients-list') + '?name=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'avocado')
        self.assertEqual(response.data[1]['name'], 'Banana')
        response = self.client.get(reverse('ingredients-list'))
        self.assertEqual(len(response.data), 3)

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

    def test_recipes_list(self):
        """Recipes list has all the necessary fields in correct formats."""

        response = self.client.get(reverse('recipes-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'][0]
        self.assertEqual(len(data), 10)
        for field in (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        ):
            with self.subTest(field=field):
                self.assertIn(field, data)
        self.assertIsInstance(data['tags'], list)
        self.assertIsInstance(data['ingredients'], list)
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['cooking_time'], int)
        self.assertIsInstance(data['author'], dict)
        self.assertIsInstance(data['is_favorited'], bool)
        self.assertIsInstance(data['is_in_shopping_cart'], bool)
        self.assertIsInstance(data['image'], str)
        self.assertIsInstance(data['name'], str)
        self.assertIsInstance(data['text'], str)

    def test_endpoints_with_invalid_tokens(self):
        """Invalid token requests return correct status codes."""

        get_endpoints = (
            reverse('users-detail', kwargs={'pk': self.testuser.id}),
            reverse('users-me'),
        )
        post_endpoints = (reverse('users-set-password'),)
        invalid_token_client = APIClient()
        invalid_token_client.credentials(HTTP_AUTHORIZATION='Token ' + 'AAA')
        for endpoint in get_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    invalid_token_client.get(endpoint).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )
        for endpoint in post_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    invalid_token_client.post(endpoint, {}).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_endpoints_without_tokens(self):
        """No token requests return correct status codes."""

        get_endpoints = (
            reverse('users-me'),
            reverse('users-subscriptions'),
            reverse('users-subscribe', kwargs={'pk': 1}),
        )
        post_endpoints = (
            reverse('users-set-password'),
            reverse('favorite', kwargs={'recipe_id': 1}),
            reverse('users-subscribe', kwargs={'pk': 1}),
            reverse('recipes-list'),
        )
        no_token_client = APIClient()
        for endpoint in get_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    no_token_client.get(endpoint).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )
        for endpoint in post_endpoints:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    no_token_client.post(
                        endpoint, {}, format='json'
                    ).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )


class AuthorizedUserTests(APITestCase):
    """Tests for authorized clients of non-admin level."""

    @classmethod
    def setUp(cls):
        cls.user_details = {
            'username': 'u',
            'email': 'u@i.com',
            'first_name': 'William',
            'last_name': 'Tell',
        }
        cls.user = User.objects.create_user(**cls.user_details)
        cls.author = User.objects.create_user(username='a', email='a@i.com')
        cls.user_client, cls.author_client = APIClient(), APIClient()
        cls.user_client.force_authenticate(cls.user)
        cls.author_client.force_authenticate(cls.author)
        cls.fake = Faker()
        cls.recipe = generate_recipe(cls.author)
        cls.recipes = [generate_recipe(author=cls.author) for _ in range(10)]

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
            "ingredients": [
                {"id": ingredient.id, "amount": self.fake.pyint()}
                for ingredient in ingredients
            ],
            "tags": [tag.id for tag in tags],
            "image": 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII=',
            "name": self.fake.sentence(),
            "text": self.fake.sentence(),
            "cooking_time": self.fake.pyint(),
        }
        response = self.author_client.post(url, recipe_presets, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), prev_recipes + 1)
        self.assertEqual(len(response.data), 10)
        for field in (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ):
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        self.assertIsInstance(response.data['tags'], list)
        self.assertIsInstance(response.data['ingredients'], list)
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['cooking_time'], int)
        self.assertIsInstance(response.data['author'], dict)
        self.assertIsInstance(response.data['is_favorited'], bool)
        self.assertIsInstance(response.data['is_in_shopping_cart'], bool)
        self.assertIsInstance(response.data['image'], str)
        self.assertIsInstance(response.data['name'], str)
        self.assertIsInstance(response.data['text'], str)

    def test_my_profile(self):
        """Test if the user profile is correct."""

        response = self.user_client.get(reverse('users-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in self.user_details.keys():
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
        creds = {'old_password': 'even_this', 'new_password': '111'}
        self.user.set_password(creds['old_password'])
        self.user.save()
        self.assertTrue(self.user.check_password(creds['old_password']))
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 400)
        creds['new_password'] = 'me'
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 400)
        creds['new_password'] = 'on_a_second_thought'
        response = self.user_client.post(url, creds)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, {})
        self.assertTrue(self.user.check_password(creds['new_password']))

    def test_favorite_endpoint(self):
        """Tests for favorite endpoint."""

        Favorite.objects.create(
            user=self.author, recipe=self.recipe
        )  # needed for recipe.id test to fail if wrong id is returned
        previous_favs = Favorite.objects.count()
        url = reverse('favorite', kwargs={'recipe_id': self.recipe.id})
        response = self.user_client.post(url, {})
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
        # self.assertEqual(response.data['id'], self.recipe.id)
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


class PaginationTests(APITestCase):
    @classmethod
    def setUp(cls):
        cls.paginated_pages = {
            reverse('users-list'): 11,
            reverse('users-subscriptions'): 10,
            reverse('recipes-list'): 10,
        }
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
        cls.recipes = [
            Recipe.objects.create(
                author=cls.subscriber,
                text=cls.fake.text(),
                name=cls.fake.sentence(),
                cooking_time=cls.fake.pyint(),
                image=cls.fake.file_path(depth=3, category='image'),
            )
            for _ in range(10)
        ]

    def test_paginated_pages(self):
        """Tests that pages that should be paginated are paginated."""

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
            self.assertEqual(len(response.data['results']), 3)
            response = self.subscriber_client.get(url, {'limit': 5, 'page': 4})
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            response = self.subscriber_client.get(url, {'limit': 5, 'page': 1})
            self.assertIsNone(response.data['previous'])
            response = self.subscriber_client.get(url, {'limit': 4, 'page': 3})
            self.assertIsNone(response.data['next'])
