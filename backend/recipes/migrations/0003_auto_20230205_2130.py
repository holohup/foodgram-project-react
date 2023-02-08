# Generated by Django 2.2.16 on 2023-02-05 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20230205_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=250, verbose_name='Ingredient name'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Publication date'),
        ),
        migrations.AlterIndexTogether(
            name='ingredient',
            index_together={('name', 'measurement_unit')},
        ),
    ]