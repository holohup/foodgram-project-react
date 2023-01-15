# Generated by Django 2.2.16 on 2023-01-15 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingridient',
            options={'verbose_name': 'Ingridient', 'verbose_name_plural': 'Ingridients'},
        ),
        migrations.AddConstraint(
            model_name='ingridient',
            constraint=models.UniqueConstraint(fields=('name', 'measurement'), name='Unique name and measurement units combo'),
        ),
    ]
