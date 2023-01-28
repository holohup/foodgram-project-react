from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from api.utils import get_grocery_list, plain_data_to_cart_items


@login_required
def download_shopping_list(request):

    data = plain_data_to_cart_items(get_grocery_list(request.user))
    if not data:
        return HttpResponse('The shopping list is empty', status_code=500)
    context = {
        'author': request.user,
        'data': data,
        'title': 'HELLO'
    }
    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename="ShoppingCart
    # .pdf"'

    return render(request, '../../recipes/templates/list.html', context)
    # return response
