# Generated by Django 2.2.16 on 2023-02-05 12:27

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Favorite',
                'verbose_name_plural': 'Favorites',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=250, verbose_name='Ingredient name')),
                ('measurement_unit', models.CharField(max_length=100, verbose_name='Measurement unit')),
            ],
            options={
                'verbose_name': 'Ingredient',
                'verbose_name_plural': 'Ingredients',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('image', models.ImageField(upload_to='recipes/', verbose_name='Picture')),
                ('text', models.TextField(verbose_name='Cooking algorithm')),
                ('pub_date', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Publication_date')),
                ('cooking_time', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1)], verbose_name='Cooking Time')),
            ],
            options={
                'verbose_name': 'Recipe',
                'verbose_name_plural': 'Recipes',
                'ordering': ['-pub_date'],
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(verbose_name='Ingredient amount')),
            ],
            options={
                'verbose_name': 'Recipe Ingredient',
                'verbose_name_plural': 'Recipe Ingredients',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Tag name')),
                ('color', models.CharField(max_length=7, unique=True, validators=[django.core.validators.RegexValidator(code='incorrect_hex_color', message='Incorrect HEX color.', regex='^#[A-Fa-f0-9]{6}$')], verbose_name='color')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='slug')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shop_cart', to='recipes.Recipe', verbose_name='Recipe in shopping cart')),
            ],
            options={
                'verbose_name': 'Shopping cart',
                'verbose_name_plural': 'Shopping carts',
            },
        ),
    ]
