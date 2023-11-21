from django.http import JsonResponse
import jwt
from api.settings import SECRET_KEY
from administration.models import User
from administration.serializers import RoleSerializer
from django.db.models import Q


class PermissionsMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def get_queries_from_point_of_sales(self, permissions, defaults):
        country_queries = list()
        pos_queries = list()
        account_queries = list()
        # set up Q objects
        for country in permissions["countries"]:
            country_queries.append(
                f"Q(country__id__exact='{country}')")
        for pos in permissions["point_of_sales"]:
            pos_queries.append(f"Q(id__exact='{pos}')")
        for account in permissions["accounts"]:
            account_queries.append(
                f"Q(account__id__exact='{account}')")

        country_queries = f' ({"|".join(country_queries)})'
        pos_queries = f' ({"|".join(pos_queries)})'
        account_queries = f' ({"|".join(account_queries)})'
        return eval(" & ".join([
            country_queries,
            #pos_queries,
            account_queries
        ]))

    def get_queries_from_products(self, permissions, defaults):
        division_queries = list()
        for division in permissions["divisions"]:
            division_queries.append(
                f"Q(division__id__exact='{division}')")

        division_queries = f' ({"|".join(division_queries)})'

        return eval(" & ".join([
            division_queries
        ]))

    def get_queries_from_divisions(self, permissions, defaults):
        division_queries = list()
        for division in permissions["divisions"]:
            division_queries.append(f"Q(id__exact='{division}')")

        division_queries = f' ({"|".join(division_queries)})'

        return eval(" & ".join([
            division_queries
        ]))

    def get_queries_from_accounts(self, permissions, defaults):
        account_queries = list()
        for account in permissions["accounts"]:
            account_queries.append(f"Q(id__exact='{account}')")

        account_queries = f' ({"|".join(account_queries)})'

        return eval(" & ".join([
            account_queries
        ]))

    def get_queries_from_weekly_sales(self, permissions, defaults):
        country_queries = list()
        pos_queries = list()
        account_queries = list()
        division_queries = list()

        # set up Q objects
        # dont leave space after or before Q()
        for country in permissions["countries"]:
            country_queries.append(
                f"Q(site_id__country__id__exact={country})")

        #pos_queries.append(
        #    f"Q(site_id__id__in={permissions['point_of_sales']})")

        for account in permissions["accounts"]:
            account_queries.append(
                f"Q(site_id__account__id__exact={account})")
        for division in permissions["divisions"]:
            division_queries.append(
                f"Q(product__division__id__exact={division})")

        # set up OR category-level comparisons
        country_queries = f' ({"|".join(country_queries)})'
        #pos_queries = f' ({"|".join(pos_queries)})'
        account_queries = f' ({"|".join(account_queries)})'
        division_queries = f' ({"|".join(division_queries)})'

        # set up AND access-level comparisons per origin

        #
        from_weekly_sales = eval(" & ".join([
            country_queries,
            #pos_queries,
            account_queries,
            division_queries
        ]))
        return from_weekly_sales

    def get_queries_from_flooring(self, permissions, defaults):
        country_queries = list()
        pos_queries = list()
        account_queries = list()
        division_queries = list()

        # set up Q objects
        for country in permissions["countries"]:
            country_queries.append(
                f"Q(point_of_sale__country__id__exact='{country}')")
        # for pos in permissions["point_of_sales"]:
        pos_queries.append(
            f"Q(point_of_sale__id__in={permissions['point_of_sales']})")
        for account in permissions["accounts"]:
            account_queries.append(
                f"Q(point_of_sale__account__id__exact='{account}')")
        for division in permissions["divisions"]:
            division_queries.append(
                f"Q(product__division__id__exact='{division}')")

        # set up OR category-level comparisons
        country_queries = f' ({"|".join(country_queries)})'
        pos_queries = f' ({"|".join(pos_queries)})'
        account_queries = f' ({"|".join(account_queries)})'
        division_queries = f' ({"|".join(division_queries)})'

        # set up AND access-level comparisons per origin
        from_weekly_sales = eval(" & ".join([
            country_queries,
            pos_queries,
            account_queries,
            division_queries
        ]))
        return from_weekly_sales

    def process_view(self, request, view_func, view_args, view_kwargs):

        try:
            # try to get the user from token
            token = request.headers["Authorization"].replace("Bearer ", "")
            user_id = jwt.decode(token, SECRET_KEY, algorithms=[
                "HS256"])["user_id"]
            user = User.objects.get(id=user_id)
            default_from_weekly_sales = Q()  # ~Q(site_id__pos_type__value='DC')
            default_from_point_of_sales = Q()
            default_from_products = Q()
            default_from_divisions = Q()
            default_from_accounts = Q()
            default_from_flooring = Q()

            if not len(user.roles.all()):
                return JsonResponse({
                    "detail": "This user has no roles assigned"
                }, status=401)

            if 1 in [x.id for x in user.roles.all()]:

                #
                queries = {
                    "from_weekly_sales": default_from_weekly_sales,
                    "from_point_of_sales": default_from_point_of_sales,
                    "from_products": default_from_products,
                    "from_divisions": default_from_divisions,
                    "from_accounts": default_from_accounts,
                    "from_flooring": default_from_flooring
                }

                #
                setattr(request, "user_read_permissions", {})
                #
                setattr(request, "read_permissions_queries", queries)
                #

                return
        except Exception as ex:
            return
        serializer = RoleSerializer(user.roles.all(), many=True)

        setattr(request, "user_roles", serializer.data)

        countries = set()
        point_of_sales = set()
        views = set()
        accounts = set()
        divisions = set()

        for role in serializer.data:
            for country in role["countries"]:
                countries.add(country["id"])
            for pos in role["point_of_sales"]:
                point_of_sales.add(pos["id"])
            for view in role["views"]:
                views.add(view["id"])
            for account in role["accounts"]:
                accounts.add(account["id"])
            for division in role["divisions"]:
                divisions.add(division["id"])
        permissions = {
            "countries": countries,
            "point_of_sales": point_of_sales,
            "views": views,
            "accounts": accounts,
            "divisions": divisions,
        }

        from_point_of_sales = self.get_queries_from_point_of_sales(
            permissions, default_from_point_of_sales)
        from_weekly_sales = self.get_queries_from_weekly_sales(
            permissions, default_from_weekly_sales)
        from_products = self.get_queries_from_products(
            permissions, default_from_products)
        from_divisions = self.get_queries_from_divisions(
            permissions, default_from_divisions)
        from_accounts = self.get_queries_from_accounts(
            permissions, default_from_accounts)
        from_flooring = self.get_queries_from_flooring(
            permissions, default_from_flooring)

        queries = {
            "from_weekly_sales": from_weekly_sales,
            "from_point_of_sales": from_point_of_sales,
            "from_products": from_products,
            "from_divisions": from_divisions,
            "from_accounts": from_accounts,
            "from_flooring": from_flooring
        }
        del permissions["point_of_sales"]
        setattr(request, "user_read_permissions", permissions)
        setattr(request, "read_permissions_queries", queries)
