from typing import List, NamedTuple

from django.conf import settings
from django.contrib.auth import get_user_model
from fpdf import FPDF

from recipes.models import Recipe, RecipeIngredient

User = get_user_model()


class ShoppingCartItem(NamedTuple):
    name: str
    measurement_unit: str
    amount: int


def get_grocery_list(user: User):
    recipes = Recipe.objects.filter(shop_cart__user=user)
    recipe_ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
    result = {}
    for item in recipe_ingredients:
        key = (item.ingredient.name, item.ingredient.measurement_unit)
        if key not in result:
            result[key] = 0
        result[key] += item.amount
    return result


def plain_data_to_cart_items(data: dict) -> List[ShoppingCartItem]:
    result = []
    for ingredient, amount in data.items():
        result.append(
            ShoppingCartItem(
                name=ingredient[0],
                measurement_unit=ingredient[1],
                amount=amount,
            )
        )
    return result


class ShoppingCartPDF:
    """Class for a shopping cart PDF with public methods."""

    def __init__(self, cell_h=None, name_cell_w=None, font_size=8) -> None:
        self.font_size = font_size
        self.pdf = self._set_up_pdf()
        self.cell_h = cell_h or self.pdf.font_size * 2.5
        self.name_cell_w = name_cell_w or self.pdf.epw * 0.65
        self.cell_w = (self.pdf.epw - self.name_cell_w) / 3
        self._render_table_header()

    def _set_up_pdf(self) -> FPDF:
        self.pdf = FPDF(format='a4')
        self.pdf.add_page()
        self.pdf.add_font(
            'Regular',
            uni=True,
            fname=f'static/fonts/{settings.SHOPPING_CART_FONT}',
        )
        self.pdf.add_font(
            'Bold',
            uni=True,
            fname=f'static/fonts/{settings.SHOPPING_CART_BOLD_FONT}',
        )
        self.pdf.set_font('Bold', size=self.font_size + 2)
        self.pdf.cell(200, 10, txt='Your Grocery List', ln=1, align='C')
        return self.pdf

    def _render_table_header(self):
        self.pdf.ln(self.cell_h)
        col_names = ('Amount', 'Units', 'Bought')
        self.pdf.set_font('Bold', size=self.font_size)
        self.pdf.cell(
            self.name_cell_w, self.cell_h, 'Name', border=1, align='C'
        )
        for col_name in col_names:
            self.pdf.cell(
                self.cell_w, self.cell_h, col_name, border=1, align='C'
            )

    def add_item(self, item: ShoppingCartItem):
        if self.pdf.will_page_break(self.cell_h * 2):
            self.pdf.ln(self.cell_h)
            self._render_table_header()
        self.pdf.ln(self.cell_h)
        self.pdf.set_font('Regular', size=self.font_size)
        self.pdf.cell(self.name_cell_w, self.cell_h, item.name, border=1)
        for attr in 'amount', 'measurement_unit':
            self.pdf.cell(
                self.cell_w,
                self.cell_h,
                str(getattr(item, attr)),
                border=1,
            )
        self.pdf.cell(self.cell_w, self.cell_h, '[  ]', border=1, align='C')

    def output(self) -> str:
        return self.pdf.output(dest='S')

    def __repr__(self) -> str:
        return 'Shopping cart PDF'


def draw_pdf(data: List[ShoppingCartItem]) -> str:

    pdf = ShoppingCartPDF(font_size=10)
    for item in data:
        pdf.add_item(item)
    return pdf.output()
