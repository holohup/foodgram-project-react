# Generated by Django 2.2.16 on 2023-01-18 11:55

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0002_auto_20230118_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='bookmarkers',
            field=models.ManyToManyField(blank=True, related_name='bookmarked', to=settings.AUTH_USER_MODEL, verbose_name='Bookmarkers'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='carts',
            field=models.ManyToManyField(blank=True, related_name='added_to_cart', to=settings.AUTH_USER_MODEL, verbose_name='Shoppers'),
        ),
    ]