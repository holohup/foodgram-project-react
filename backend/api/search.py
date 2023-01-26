from urllib.parse import unquote
from rest_framework.filters import SearchFilter


class UnquoteSearchFilter(SearchFilter):
    def get_search_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')
        params = unquote(params)
        params = params.replace(',', ' ')
        return params.split()
