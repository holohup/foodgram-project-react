import io

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from api.utils import draw_pdf, get_grocery_list, plain_data_to_cart_items


@login_required
def download_shopping_list(request):
    data = plain_data_to_cart_items(get_grocery_list(request.user))
    if not data:
        return HttpResponse('The shopping list is empty', status=404)
    buffer = io.BytesIO(bytes(draw_pdf(data)))
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ShoppingCart.pdf"'
    return response
