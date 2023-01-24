# from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscription

User = get_user_model()


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

        get_endpoints = (reverse('users-me'),)
        post_endpoints = (
            reverse('users-set-password'),
            reverse('favorite', kwargs={'recipe_id': 1}),
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
                    no_token_client.post(endpoint, {}).status_code,
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
        cls.recipe = Recipe.objects.create(
            author=cls.author,
            text=cls.fake.text(),
            name=cls.fake.sentence(),
            cooking_time=cls.fake.pyint(),
            image=cls.fake.file_path(depth=3, category='image'),
        )

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

        Favorite.objects.create(user=self.author, recipe=self.recipe) #needed for recipe.id test to fail if wrong id is returned
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


class PaginationTests(APITestCase):
    @classmethod
    def setUp(cls):
        cls.fake = Faker()
        usernames = cls.fake.words(10, unique=True)
        cls.users = [
            User.objects.create(
                username=username,
                email=username + '.' + cls.fake.email(),
                first_name=cls.fake.first_name(),
                last_name=cls.fake.last_name(),
                password=cls.fake.password(),
            )
            for username in usernames
        ]

    def test_users_pagination(self):
        response = self.client.get(reverse('users-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in 'count', 'next', 'previous', 'results':
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        self.assertEqual(len(response.data), 4)
        url = reverse('users-list')
        response = self.client.get(url, {'limit': 3, 'page': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(
            response.data['next'],
            'http://testserver/api/users/?limit=3&page=4',
        )
        self.assertEqual(
            response.data['previous'],
            'http://testserver/api/users/?limit=3&page=2',
        )
        self.assertEqual(len(response.data['results']), 3)
        response = self.client.get(url, {'limit': 5, 'page': 3})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(url, {'limit': 5, 'page': 1})
        self.assertIsNone(response.data['previous'])
        response = self.client.get(url, {'limit': 5, 'page': 2})
        self.assertIsNone(response.data['next'])
