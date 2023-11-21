import urllib
from django.db.models import Q


class FiltersMiddleware:
    qs_from_ws = {
        "product_group": lambda x: Q(product__group=x),
        "division": lambda x: Q(product__division=x),
        "region": lambda x: Q(site_id__region=x),
        "country": lambda x: Q(site_id__country=x),
        "account": lambda x: Q(site_id__account=x),
        "store": lambda x: Q(site_id=x),
        "city": lambda x: Q(site_id__city=x),
        "country_zones": lambda x: Q(site_id__zone=x),
    }
    qs_from_flooring = {
        "product_group": lambda x: Q(product__group=x),
        "division": lambda x: Q(product__division=x),
        "region": lambda x: Q(point_of_sale__region=x),
        "country": lambda x: Q(point_of_sale__country=x),
        "account": lambda x: Q(point_of_sale__account=x),
        "store": lambda x: Q(point_of_sale=x),
        "city": lambda x: Q(point_of_sale__city=x),
        "country_zones": lambda x: Q(point_of_sale__zone=x),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        path_split = request.get_full_path().split("?")
        if len(path_split) or len(path_split[-1]):
            query_params = urllib.parse.parse_qs(path_split[-1])
        else:
            return

        for k, _ in query_params.items():
            query_params[k] = query_params[k][0].split(",")
        queries = Q()
        for key, values in query_params.items():
            if not key in self.qs_from_ws:
                continue
            category_level_queries = Q()  # list()
            for value in values:
                category_level_queries = category_level_queries | self.qs_from_ws[key](
                    value)
            queries = queries & category_level_queries

        setattr(request, "filters", queries)

        queries = Q()
        for key, values in query_params.items():
            if not key in self.qs_from_flooring:
                continue
            category_level_queries = Q()  # list()
            for value in values:
                category_level_queries = category_level_queries | self.qs_from_flooring[key](
                    value)
            queries = queries & category_level_queries

        setattr(request, "filters_from_flooring", queries)
