from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from users.models import Subscription

User = get_user_model()


class UnauthorizedUserTests(APITestCase):
    def setUp(self):
        """Tests presets."""
        pass

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
        response = self.client.get(reverse('customuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in 'count', 'next', 'previous', 'results':
            with self.subTest(field=field):
                self.assertIn(field, response.data)
        user_data = response.data['results'][0]
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
            'password': 'Qwerffty123Qwerty123'
        }
        response = self.client.post(reverse('customuser-list'), payload)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload['first_name'] = 'Willy'
        response = self.client.post(reverse('customuser-list'), payload)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertNotIn('is_subscribed', data)
        payload['id'] = User.objects.last().id
        for field in data.keys():
            with self.subTest(field=field):
                self.assertEqual(payload[field], data[field])



class AuthorizedUserTests(APITestCase):
    """Tests for authorized clients of non-admin level."""

    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@i.com')
        self.author = User.objects.create_user(username='a', email='a@i.com')
        self.user_client, self.author_client = APIClient(), APIClient()
        self.user_client.force_authenticate(self.user)
        self.author_client.force_authenticate(self.author)

    def test_subscriptions_on_users_page(self):
        """Create a subscription, check that it shows on /users/ endpoint."""

        Subscription.objects.create(user=self.user, author=self.author)
        url = reverse('customuser-list')
        user_results = self.user_client.get(url).data['results']
        author_results = self.author_client.get(url).data['results']
        for result in user_results:
            if result['id'] == self.author.id:
                self.assertTrue(result['is_subscribed'])
        for result in author_results:
            if result['id'] == self.user.id:
                self.assertFalse(result['is_subscribed'])
