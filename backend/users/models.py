from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    email = models.EmailField('email address', unique=True, max_length=254)
    username = models.CharField('username', max_length=150)
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    password = models.CharField('password', max_length=150)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    """Subscription model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Recipes author',
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'user'), name='Unique subscription'
            ),
            models.CheckConstraint(
                name='Prevent self subscription',
                check=~models.Q(user=models.F('author')),
            ),
        )

    def __str__(self):
        return f'{self.user} subscription on {self.author}'
