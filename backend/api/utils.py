from operator import attrgetter
from typing import List, NamedTuple

from django.conf import settings
from django.db.models import Sum
from fpdf import FPDF

from recipes.models import RecipeIngredient
from users.models import User


class ShoppingCartItem(NamedTuple):
    name: str
    measurement_unit: str
    amount: int


class ShoppingCartPDF:
    """Class for a shopping cart PDF with public methods."""

    fonts_dir = f'{settings.STATIC_ROOT}/fonts'
    default_cell_h_ratio = 1.5
    default_n_cell_w_ratio = 0.65
    default_cell_w_ratio = 1 / 3
    default_format = 'a4'
    default_font = 'DejaVuSans.ttf'
    default_bold_font = 'DejaVuSansCondensed-Bold.ttf'
    default_title_increment = 5
    grocery_list_title = 'Your Grocery List'
    page_break_threshold = 2
    title_cell_size = 200

    def __init__(self, cell_h=None, n_cell_w=None, font_size=8) -> None:
        """Initialization and setup."""

        self.font_size = font_size
        self.pdf = self._set_up_pdf()
        pdf_epw = self.pdf.epw
        self.cell_h = cell_h or font_size * self.default_cell_h_ratio
        self.n_cell_w = n_cell_w or pdf_epw * self.default_n_cell_w_ratio
        self.cell_w = (pdf_epw - self.n_cell_w) * self.default_cell_w_ratio
        self._render_table_header()

    def __repr__(self) -> str:
        """How a class object will be displayed."""

        return 'Shopping cart PDF'

    def _set_up_pdf(self) -> FPDF:
        """Setting up the pdf file."""

        self.pdf = FPDF(format=self.default_format)
        self.pdf.add_page()
        self.pdf.add_font(
            'Regular',
            uni=True,
            fname=f'{self.fonts_dir}/{self.default_font}',
        )
        self.pdf.add_font(
            'Bold',
            uni=True,
            fname=f'{self.fonts_dir}/{self.default_bold_font}',
        )
        self.pdf.set_font(
            'Bold', size=self.font_size + self.default_title_increment
        )
        self.pdf.cell(
            self.title_cell_size,
            self.font_size,
            txt=self.grocery_list_title,
            ln=1,
            align='C',
        )
        return self.pdf

    def _render_table_header(self):
        """Rendering the table header."""

        self.pdf.ln(self.cell_h)
        col_names = ('Amount', 'Units', 'Bought')
        self.pdf.set_font('Bold', size=self.font_size)
        self.pdf.cell(self.n_cell_w, self.cell_h, 'Name', border=1, align='C')
        for col_name in col_names:
            self.pdf.cell(
                self.cell_w, self.cell_h, col_name, border=1, align='C'
            )

    def add_item(self, item: ShoppingCartItem):
        """Add an item to the table."""

        if self.pdf.will_page_break(self.cell_h * self.page_break_threshold):
            self.pdf.ln(self.cell_h)
            self._render_table_header()
        self.pdf.ln(self.cell_h)
        self.pdf.set_font('Regular', size=self.font_size)
        self.pdf.cell(self.n_cell_w, self.cell_h, ' ' + item.name, border=1)
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


def get_grocery_list(user: User) -> List[ShoppingCartItem]:
    """Get user's grocery list in a human-readable form."""

    recipe_ingredients = (
        RecipeIngredient.objects.filter(recipe__shop_carts__user=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(amount=Sum('amount'))
    )
    return [
        ShoppingCartItem(
            item['ingredient__name'],
            item['ingredient__measurement_unit'],
            item['amount'],
        )
        for item in recipe_ingredients
    ]


def draw_pdf(data: List[ShoppingCartItem]) -> str:
    """Create a pdf and return it as a string."""

    pdf = ShoppingCartPDF(font_size=10)
    for item in sorted(data, key=attrgetter('name')):
        pdf.add_item(item)
    return pdf.output()
