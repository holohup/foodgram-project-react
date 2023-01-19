from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UnauthorizedUserTests(APITestCase):
    def setUp(self):
        """Tests presets."""
        pass

    def test_get_token_and_logout(self):
        """Check if we can obtain a working token, and we can delete it."""

        user = User.objects.create(
            email='hello@space.com'
        )
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
            status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        self.assertEqual(
            self.client.post(logout_url, {}).status_code,
            status.HTTP_204_NO_CONTENT)
