from django.contrib.auth import get_user_model
from django.test import TestCase


class CustomUserTests(TestCase):
    """Tests if CustomUser model works as intented."""

    def setUp(self):
        self.User = get_user_model()

    def test_create_user(self):
        """Tests non-admin user creation."""

        user = self.User.objects.create_user(
                username='Nekrasov',
                email='Nekrasov@yandex.ru',
                password='classic_password'
            )
        self.assertEqual(user.username, 'Nekrasov')
        self.assertEqual(user.email, 'Nekrasov@yandex.ru')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Tests superuser creation."""

        admin_user = self.User.objects.create_superuser(
            username='dostoevsky',
            email='dost_1821@rambler.ru',
            password='esliboganettovsedozvoleno'
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
        user = self.User.objects.create_user(
                username='Long',
                email='my_real_name@gmail.com',
                first_name=long_firstname
            )
        self.assertEqual(user.first_name, long_firstname)
