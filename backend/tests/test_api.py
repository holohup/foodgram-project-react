from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserViewSetTest(APITestCase):
    def setUp(self):
        """Tests presets."""
        pass

    def test_get_token(self):
        user = User.objects.create(
            username='testUser', email='hello@space.com'
        )
        user.set_password('testPassword')
        user.save()
        data = {
            'email': 'hello@space.com',
            'password': 'testPassword',
        }
        response = self.client.post(reverse('get_token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)
        token = response.data['auth_token']
        self.assertIsNotNone(token)
        # TODO: Create a verify point to check if the token is working
