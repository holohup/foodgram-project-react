from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    first_name = models.CharField(('first name'), max_length=150, blank=False)
    last_name = models.CharField(('last name'), max_length=150, blank=False)
    email = models.EmailField(('email address'), blank=False)

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'


User = get_user_model()


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Recipes author'
    )

    def __str__(self):
        return f'{self.user} subscription on {self.author}'

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'], name='Unique subscription'
            ),
            models.CheckConstraint(
                name='Prevent self subscription',
                check=~models.Q(user=models.F('author')),
            ),
        ]
