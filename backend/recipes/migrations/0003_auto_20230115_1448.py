# Generated by Django 2.2.16 on 2023-01-15 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20230115_1220'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='color',
            field=models.CharField(default='#000000', max_length=7, verbose_name='color'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tag',
            name='name',
            field=models.CharField(default='test_name', max_length=64, verbose_name='Tag name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tag',
            name='recipe',
            field=models.ManyToManyField(to='recipes.Recipe'),
        ),
        migrations.AddField(
            model_name='tag',
            name='slug',
            field=models.SlugField(default='test_slug', verbose_name='slug'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.TextField(verbose_name='Cooking algorithm'),
        ),
    ]
