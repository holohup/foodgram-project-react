from csv import DictReader
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка данных'

    def handle(self, *args, **options):
        print('Загрузка данных...')
        with open(
            '../data/ingredients.csv', encoding='utf-8', newline=''
        ) as ifile:
            reader = DictReader(ifile, fieldnames=['name', 'measurement_unit'])
            bulk_data = [
                Ingredient(
                    name=row['name'], measurement_unit=row['measurement_unit']
                )
                for row in reader
            ]
            Ingredient.objects.bulk_create(bulk_data)
