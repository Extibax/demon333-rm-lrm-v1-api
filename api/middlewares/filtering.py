import imp
import urllib
from django.db.models import Max
from django.http import JsonResponse
from product.models import Week, WeeklySale
from service import logging
from .query_strings import query_keys


class FilteringMiddleware:
    """Middleware in charge on translating query param filtering and read permissions based on storage cache"""

    # filter keys should have standardized names as module__model, this is for validation of params

    permission_keys = {
        "point_of_sales": {"name": "point_of_sale"},
        "accounts": {"name": "point_of_sale_account"},
        "divisions": {"name": "product_division"},
        "countries": {"name": "point_of_sale_country"},
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):

        try:
            # try to get the user from token
            token = request.headers["Authorization"].replace("Bearer ", "")

        except Exception as ex:
            return
        ##########################################################
        # QUERY PARAMS
        ##########################################################
        path_split = request.get_full_path().split("?")
        if len(path_split) or len(path_split[-1]):
            query_params = urllib.parse.parse_qs(path_split[-1])
        else:
            return
        logging.info(f"[FILTERING] parsed query params {query_params}")
        for k, _ in query_params.items():
            query_params[k] = query_params[k][0].split(",")

        # VALIDATE AND TRANSFORM QUERY VALUES
        for key, values in query_params.items():
            if not key in query_keys:
                return JsonResponse({
                    "detail": f"invalid query param: {key}. valid options are: {[k for k,_ in query_keys.items()]}"
                }, status=400)

            # IF TYPE SHOULD BE INT... CONVERT
            if query_keys[key].get("type", str) == int:
                query_params[key] = [int(x) for x in values]
        setattr(request, "qparams", query_params)
        logging.info(f"[FILTERING] casted query params {query_params}")
        pandas_query_strings = [
            f"{key} in {values}" for key, values in query_params.items() if (query_keys[key]["for_pandas"] or query_keys[key]["for_admin"]) and not query_keys[key]["is_date_range"]]
        for key, values in query_params.items():
            if request.resolver_match.app_name == "administration" and query_keys[key]["is_date_range"] and key == "from_date":
                pandas_query_strings.append(
                    f"{key} >= '{values[0]} 00:00:000000 +00:00'")
            if request.resolver_match.app_name == "administration" and query_keys[key]["is_date_range"] and key == "to_date":
                pandas_query_strings.append(
                    f"{key} <= '{values[0]} 00:00:000000 +00:00'")
        # if query_keys[key]["for_admin"]:
        #     pandas_query_strings = [
        #         f"{key} = {values}" for key, values in query_params.items()]

        query_filters = " & ".join(pandas_query_strings)
        setattr(request, "query_filters", query_filters)
        logging.info(
            f"[FILTERING] pandas (from query params) filters {query_filters}")
        ##########################################################
        # USER READ PERMISSIONS
        ##########################################################
        pandas_user_permissions = []
        permission_filters = ""
        if request.resolver_match.app_name == "reports":
            try:
                permissions = request.user_read_permissions
            except:
                return
            if not permissions == {}:  # superuser
                for k, v in permissions.items():
                    if k in self.permission_keys:
                        pandas_user_permissions.append(
                            f"{self.permission_keys[k]['name']} in {list(v)}")

            permission_filters = " & ".join(pandas_user_permissions)

            logging.info(
                f"[FILTERING] pandas (permissions) filters {permission_filters}")
        setattr(request, "permission_filters", permission_filters)

        ##########################################################
        # JOIN ALL POSSIBLE FILTERS
        ##########################################################

        all_filters = " & ".join(
            [x for x in [query_filters, permission_filters] if not x == ""])

        if not len(query_filters)+len(permission_filters) > 0:
            all_filters = None

        if request.resolver_match.app_name == "reports":
            default_filter = " and ".join(
                [f"{k}!=1" for k, v in query_keys.items() if v["for_pandas"] and v["filter_defaults"]])
            all_filters = default_filter if all_filters == None else f"({default_filter})and({all_filters})"

        setattr(request, "all_filters", all_filters)

        ##########################################################
        # Week ranges
        ##########################################################

        # max_week_available = WeeklySale.objects.aggregate(
        #    max=Max("week_object"))["max"]
        max_week_available = 205
        _to = query_params.get("week_end", [max_week_available])[0]
        _from = query_params.get("week_start", [_to-11])[0]

        if not _from <= _to:
            return JsonResponse({
                "detail": f"invalid week range. week_start ({_from}) must be lower or equal to week_end ({_to})"

            }, status=400)
        if _to > max_week_available:
            return JsonResponse({
                "detail": f"invalid week range. week_end ({_to}) must be lower or equal to max week available ({max_week_available})"
            }, status=400)
        logging.info(
            f"[FILTERING] week from {_from} to {_to}")
        maxes = Week.objects.get(id=_to)
        setattr(request, "range", {
            "from": _from,
            "to": _to,
            "first_week_of_year": _to - Week.objects.get(id=_to).week + 1,
            "max_week": maxes.week,
            "max_year": maxes.year
        })
