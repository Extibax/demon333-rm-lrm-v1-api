
import json
from locale import normalize
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Value
from django.db.models import Case
from django.db.models import When
from django.db.models import F
from django.db.models import StdDev
from django.db.models import DecimalField
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Max
from django.db.models import ExpressionWrapper
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime
from datetime import date
from rest_framework.decorators import api_view
import pandas as pd
import numpy as np
from service import logging
from product.models import Product, WeeklySale
from product.models import Group
from product.models import Division
from locations.models import Region
from locations.models import Country
from store.models import Account, PointOfSale
# from product.serializers import WeeklySaleSerializer

from product.serializers import WeeklySaleSimpleSerializer
from reports.models import Flooring
from reports.serializers import FlooringSerializer
from api.common.helpers import normalize_fields_from_list
from service import Thread
from .views.docs import manual_params
from hashlib import md5
from service.storage_cache import StorageCache
from api.settings import elastic_cache


def get_sales_data2(query, week, fields, permissions, user_role=None):
    logging.info(f"[THREAD] fetching week {week}")
    # d = WeeklySaleSimpleSerializer(
    d = WeeklySale.objects.filter(
        query & Q(week_object=week)).values(*fields)  # , many=True)
    #d = d.data
    key = "queries_"+md5(d.query.__str__().encode("utf-8")).hexdigest()
    content, status = StorageCache.get_pickle(key)

    if status:

        return content
    # if content != None:
    #    d = json.loads(content.decode("utf-8"))
    #    logging.info(f"[THREAD] fetched from cache {week}")
    # else:

    product_fields = ("id", "group", "group__value",
                      "division", "division__value")
    pos_fields = ("id", "city", "city__name", "account", "account__name", "zone", "zone__name",
                  "region", "region__name", "country", "country__name")

    products = pd.DataFrame(Product.objects.all().values(*product_fields))
    pos = pd.DataFrame(PointOfSale.objects.all().values(*pos_fields))

    df = pd.DataFrame(d)
    joined = df.set_index("product").join(products.set_index(
        "id")).reset_index().rename(columns={"index": "product"}).set_index("site_id").join(pos.set_index("id")).reset_index().rename(columns={"index": "site_id"})

    # if user_role and user_role != 1:
    queries = list()

    queries.append(
        f"country in {list(permissions['countries'])}")
    queries.append(f"division in {list(permissions['divisions'])}")
    queries.append(f"account in {list(permissions['accounts'])}")
    queries.append(f"site_id in {list(permissions['point_of_sales'])}")
    joined = joined.query(" & ".join(queries))

    joined = joined.drop(columns=list(
        pos_fields+product_fields), errors="ignore")

    #    elastic_cache.set(key, json.dumps(d))
    logging.info(f"[THREAD] fetched {week}")
    StorageCache.set_pickle(key, joined)
    return joined


def get_sales_data(q, week, fields):
    logging.info(f"[THREAD] fetching week {week}")
    # d = WeeklySaleSimpleSerializer(
    d = WeeklySale.objects.filter(
        q & Q(week_object=week)).values(*fields)  # , many=True)
    #d = d.data
    #key = "queries:"+md5(d.query.__str__().encode("utf-8")).hexdigest()
    #content = elastic_cache.get(key)
    # if content != None:
    #    d = json.loads(content.decode("utf-8"))
    #    logging.info(f"[THREAD] fetched from cache {week}")
    # else:
    d = list(d)
    #    elastic_cache.set(key, json.dumps(d))
    logging.info(f"[THREAD] fetched {week}")
    return d


class DashboardDataView(APIView):
    """
    Get dashboard data by report type (productGroup, division, product, account, store)
    Used to be <b> /getCustomerData, /getDivisionData, /getPointOfSaleData, /getProductData, /getProductGroupData </b>
    """
    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request, group: str) -> Response:
        year = datetime.now().year

        groups_id = {
            "productGroup": "product__group",
            "division": "product__division",
            "product": "product",
            "account": "site_id__account",
            "store": "site_id",
            "ranking": "site_id",
        }
        groups = {
            "productGroup": "product__group__value",
            "division": "product__division__value",
            "product": "product__sku",
            "account": "site_id__account__name",
            "store": "site_id__gscn_site_name",
            "ranking": "site_id__gscn_site_name"
        }
        if not group in groups:
            return JsonResponse({"detail": f"{group} is not a valid group"}, status=400)
        #logging.info(f"[DATA] Calculating total sold units")
        # totalSoldUnits = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters) \
        #    .values("sold_units") \
        #    .aggregate(total_sold_units=Sum("sold_units", filter=Q(year=year)))

        logging.info(f"[DATA] Starting threads")
        data = list()
        threads = list()

        # get_sales_data2(request.filters, 180, ("inventory", "product",
        #                "year", "week", "week_object", "sold_units", "site_id"), request.user_read_permissions)

        for week in list(range(181-12, 181+1))+list(range(181-12-52, 181+1-52)):

            thread = Thread(target=get_sales_data2, args=(request.filters, week, ("inventory", "product", "year", "week",
                            "week_object", "sold_units", "site_id"), request.user_read_permissions))  # "site_id__site_id", groups_id[group], groups[group])))
            threads.append(thread)
            thread.start()

        for thread in threads:
            data.append(thread.join())

        logging.info(f"[DATA] concatenating lists")

        df = pd.concat(data)

        logging.info(f"[DATA] GETTING EXTRA DATA")

        pos_data = pd.DataFrame(PointOfSale.objects.values(
            "id", "gscn_site_name", "site_id", "account")).rename(columns={"site_id": "site_id__site_id"})
        account_data = pd.DataFrame(Account.objects.values("id", "name"))
        product_data = pd.DataFrame(Product.objects.values(
            "id", "sku", "division", "division__value", "group__value", "group"))

        df = df.set_index("site_id").join(pos_data.set_index(
            "id")).reset_index().rename(columns={"index": "site_id", "gscn_site_name": "site_id__gscn_site_name"})
        df = df.set_index("account").join(account_data.set_index(
            "id")).reset_index().rename(columns={"name": "site_id__account__name", "index": "site_id__account"})
        df = df.set_index("product").join(product_data.set_index(
            "id")).reset_index().rename(columns={"sku": "product__sku", "index": "product", "division__value": "product__division__value", "division": "product__division", "group__value": "product__group__value", "group": "product__group"})

        logging.info(f"[DATA] computing")
        df[(df["year"] == df["year"].max())].groupby(
            groups[group])["sold_units"].sum()

        cy_current_week_sell_out = df[(df["week"] == df["week"].max()) & (
            df["year"] == df["year"].max())].groupby(groups[group])["sold_units"].sum()
        cy_current_week_sell_out.name = "cy_current_week_sell_out"
        cy_current_year_sell_out = df[(df["year"] == df["year"].max())].groupby(
            groups[group])["sold_units"].sum()
        cy_current_year_sell_out.name = "cy_current_year_sell_out"
        ly_current_week_sell_out = df[(df["week"] == df["week"].max()) & (
            df["year"] == df["year"].max()-1)].groupby(groups[group])["sold_units"].sum()
        ly_current_week_sell_out.name = "ly_current_week_sell_out"
        ly_current_year_sell_out = df[(
            df["year"] == df["year"].max()-1)].groupby(groups[group])["sold_units"].sum()
        ly_current_year_sell_out.name = "ly_current_year_sell_out"

        last_month_sell_out_average = df[(df["week"] <= df["week"].max()) & (df["week"] >= df["week"].max(
        )-3) & (df["year"] == df["year"].max())].groupby(groups[group])["sold_units"].mean()
        last_month_sell_out_average.name = "last_month_sell_out_average"

        cy_current_year_inventory = df[(df["year"] == df["year"].max())].groupby(
            groups[group])["inventory"].sum()
        cy_current_year_inventory.name = "cy_current_year_inventory"

        report = pd.concat([cy_current_week_sell_out, cy_current_year_sell_out,
                           ly_current_week_sell_out, cy_current_year_inventory, ly_current_year_sell_out, last_month_sell_out_average], axis=1)

        report["yearly_growth_rate"] = 100*(report["cy_current_year_sell_out"] -
                                            report["ly_current_year_sell_out"])/report["ly_current_year_sell_out"]

        if group not in ["best", "worst"]:
            report["weekly_growth_rate"] = 100*(report["cy_current_week_sell_out"] -
                                                report["ly_current_week_sell_out"])/report["ly_current_week_sell_out"]
        report["portion"] = 100*report["cy_current_year_sell_out"] / \
            report["cy_current_year_sell_out"].sum()

        logging.info(f"[DATA] conditionals")
        if group == "account":
            report["pos"] = df[(df["week"] == df["week"].max()) & (df["year"] == df["year"].max())].value_counts(
                ["site_id__site_id", groups[group]]).reset_index().groupby(groups[group]).sum().rename(columns={0: "pos_count"})["pos_count"]
            report["maxWeek"] = df[df["year"] == df["year"].max()].groupby(groups[group])[
                "week"].max()
            #report["id"] = df
        if group == "store" or group == "ranking":

            logging.info(f"[DATA] joining for site id")

            report = report.join(df.rename(columns={"site_id__site_id": "site_id"})
                                 [[groups[group], "site_id"]].drop_duplicates().set_index(groups[group]))
            # report["maxWeek"] = df[df["year"] == df["year"].max()].groupby(groups[group])[
            #    "week"].max()
        if group == "ranking":
            cy_last_week_inventory = df[(df["year"] == df["year"].max()) & (
                df["week"] == df["week"].max()-1)].groupby(groups[group])["inventory"].sum()

            report["LastWeekInventory"] = cy_last_week_inventory

            report["account"] = df.value_counts(["site_id__gscn_site_name", "site_id__account__name"]).reset_index(
            ).set_index("site_id__gscn_site_name")["site_id__account__name"]
            report = report.rename(columns={group: groups[group]})
        logging.info(f"[DATA] getting ids")
        report["id"] = df.value_counts([groups[group], groups_id[group]]).reset_index(
        ).set_index(groups[group])[groups_id[group]]

        # return Response(list(ormResponse))
        logging.info(f"[DATA] normalizing")
        del df
        del data

        report = report.fillna(0, inplace=True)
        report.replace([np.inf, -np.inf], 0, inplace=True)

        response = report.reset_index().to_dict("records")

        if group == "ranking":
            group = "store"
            normalize = {
                groups[group]: "store",
                "yearly_growth_rate": "growthRateYearly",
                "last_month_sell_out_average": "avgSales4W",
                "cy_current_year_sell_out": "yearlySelloutCY",
                "cy_current_week_sell_out": "weeklySelloutCW",
                "ly_current_year_sell_out": "yearlySelloutLY",
                "ly_current_week_sell_out": "weeklySelloutLW",
                "cy_current_year_inventory": "TotalInventory",
            }
            report = report.sort_values(
                "cy_current_week_sell_out", ascending=False)
            best = report.iloc[:10].reset_index().to_dict("records")
            worst = report.iloc[-10:].reset_index().to_dict("records")
            return Response({
                "best": normalize_fields_from_list(best, normalize),
                "worst": normalize_fields_from_list(worst, normalize)
            })

        normalize = {
            groups[group]: group,
            "yearly_growth_rate": "growthRateYearly",
            "weekly_growth_rate": "growthRateWeekly",
            "last_month_sell_out_average": "avgSales4W",
            "cy_current_year_sell_out": "yearlySelloutCY",
            "cy_current_week_sell_out": "weeklySelloutCW",
            "ly_current_year_sell_out": "yearlySelloutLY",
            "ly_current_week_sell_out": "weeklySelloutLW",
            "cy_current_year_inventory": "inventory",

        }

        normalized = normalize_fields_from_list(response, normalize)
        logging.info(f"[DATA] records to return {len(normalized)}")
        logging.info(f"[DATA] Returning response")

        return Response(normalized)


class DashboardRankingView(APIView):
    """
    Get dashboard ranking data by best or worst
    Used to be <b> /getTopTenStores?top=worst and /getTopTenStores?top=best </b>
    """
    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request, top: str) -> Response:
        year = datetime.now().year

        totalSoldUnits = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters) \
            .values("sold_units") \
            .aggregate(total_sold_units=Sum("sold_units", filter=Q(year=year)))

        ormResponse = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters) \
            .values("site_id__account__name", "site_id__gscn_site_name") \
            .annotate(
            maxWeek=Max("week", filter=Q(year=year)),
            totalInventory=Sum("inventory", filter=Q(year=year)),
            yearlySelloutCY=Sum("sold_units", filter=Q(year=year)),
            yearlySelloutLY=Sum("sold_units",
                                filter=Q(year=year-1)),
            lastWeekSellout=Sum("sold_units",
                                filter=Q(year=year) & Q(week=Value('maxWeek'))),
            lastWeekInventory=Sum("inventory",
                                  filter=Q(year=year) & Q(week=Value('maxWeek'))),
            avgSales4W=Avg("sold_units",
                           filter=Q(year=year) & Q(week__range=(Value('maxWeek')-3, Value('maxWeek')))),
        ).annotate(
            yearlySelloutCY=Case(When(yearlySelloutCY=None, then=Value(0, output_field=DecimalField(
                decimal_places=2))), default=ExpressionWrapper(F('yearlySelloutCY'), output_field=DecimalField(decimal_places=2))),
            yearlySelloutLY=Case(When(yearlySelloutLY=None, then=Value(0, output_field=DecimalField(
                decimal_places=2))), default=ExpressionWrapper(F('yearlySelloutLY'), output_field=DecimalField(decimal_places=2))),
            lastWeekSellout=Case(When(lastWeekSellout=None, then=Value(0, output_field=DecimalField(
                decimal_places=2))), default=ExpressionWrapper(F('lastWeekSellout'), output_field=DecimalField(decimal_places=2))),
            avgSales4W=Case(When(avgSales4W=None, then=Value(0, output_field=DecimalField(
                decimal_places=2))), default=ExpressionWrapper(F('avgSales4W'), output_field=DecimalField(decimal_places=2)))
        ).annotate(
            growthRateYearly=(100 * (F('yearlySelloutCY') -
                              F('yearlySelloutLY')) / F('yearlySelloutLY')),
            portion=((100 * F('yearlySelloutCY') /
                     ExpressionWrapper(Value(totalSoldUnits['total_sold_units'], output_field=DecimalField(decimal_places=2)), output_field=DecimalField(decimal_places=2))))
        )
        if top == "best":
            ormResponse = ormResponse.order_by('-lastWeekSellout')[:10]
        else:
            ormResponse = ormResponse.order_by('lastWeekSellout')[:10]

        return Response(normalize_fields_from_list(list(ormResponse), {
            "site_id__account__name": "account",
            "site_id__gscn_site_name": "store"
        }))


class DashboardRunRateView(APIView):
    """
    Get dashboard runrate data by filter (division, range)
    Used to be <b> /getRunRateData?filter=VIEW, /getRunRateData?filter=RANGE and /getRunRateData?filter=GLOBAL </b>
    """
    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request, filter: str) -> Response:
        year = datetime.now().year

        week_start = int(request.GET.get('week_start', 0))
        week_end = int(request.GET.get('week_end', 0))

        groups = {
            "range": "product__product_range__value",
            "division": "product__division__value"
        }

        ormResponse = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year) & Q(week__range=(week_start, week_end))) \
            .values(groups[filter]) \
            .annotate(
                sellout=Sum(
                    Case(
                        When(sold_units=None, then=0),
                        default='sold_units'
                    )),
                totalInventory=Sum(
                    Case(
                        When(inventory=None, then=0),
                        default='inventory'
                    )),
                flooring=Sum(
                    Case(
                        When(inventory=None, then=0),
                        When(inventory__gt=0, then=1),
                        default='inventory'
                    )),
        ).annotate(
            runrate=ExpressionWrapper(F('sellout'), output_field=DecimalField(
                decimal_places=2)) / ExpressionWrapper(F('flooring'), output_field=DecimalField(decimal_places=2)),
        )
        if filter == "division":
            ormResponse = ormResponse.annotate(
                year=F('year'),
                week=F('week'),
                product=F('product__sku')
            )

        return Response(normalize_fields_from_list(list(ormResponse), {
            groups[filter]: filter,
        }))


class DashboardHistoryView(APIView):
    """
    Get dashboard history data.
    Used to be <b> /getSellOutWeeklyGraph, /getSellOutYearlyGraph and /getInventoryGraph. </b>
    """

    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request) -> Response:
        year = datetime.now().year

        week_start = int(request.GET.get('week_start', 25-12))
        week_end = int(request.GET.get('week_end', 25))

        historyYearly = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters) \
            .values("year", "week") \
            .aggregate(
                salesCurrentYear=Sum('sold_units',
                                     filter=Q(year=year)),
                salesLastYear=Sum('sold_units',
                                  filter=Q(year=year-1))
        )

        historyWeekly = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year) & Q(week__range=(week_start, week_end))) \
            .values("year", "week") \
            .annotate(
            historySales=Sum('sold_units'),
            historyInventory=Sum('inventory')
        ).order_by(
            -F('week')
        )

        if historyYearly["salesCurrentYear"] == None:
            historyYearly["salesCurrentYear"] = 0

        if historyYearly["salesLastYear"] == None:
            historyYearly["salesLastYear"] = 1

        ormResponse = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year)) \
            .values("year") \
            .annotate(
            maxWeek=Max('week',
                        filter=Q(year=year) & Q(week__gte=week_start) & Q(week__lte=week_end))
        ).annotate(
            growthRateYearly=Value(
                (historyYearly["salesCurrentYear"] - historyYearly["salesLastYear"]) / historyYearly["salesLastYear"]),
            growthRateWeekly=Value(
                (historyWeekly[0]["historySales"] - historyWeekly[1]["historySales"]) / historyWeekly[1]["historySales"]),
            achievementRateYearly=Value(
                100 * (1.2 * (historyYearly["salesCurrentYear"] / historyYearly["salesLastYear"]))),
            achievementRateWeekly=Value(100 * (
                1.2 * (
                    historyWeekly[0]["historySales"] /
                    historyWeekly[1]["historySales"]
                )
            ))
        )
        # [x["historySales"] for x in historySalesWeekly]
        return Response({"historyYearly": historyYearly,
                         "historyWeekly": list(historyWeekly),
                         "extraData": list(ormResponse)})


class DashboardHistoryGraphView(APIView):
    """
    Get dashboard history graph data.
    Used to be <b> /getGraphDataAchivementRate and /getGraphDataGrossRate. </b>
    """
    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request) -> Response:
        year = datetime.now().year

        week_start = int(request.GET.get('week_start', 25-12))
        week_end = int(request.GET.get('week_end', 25))

        historyLastWeek = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year) & Q(week__range=(week_start-1, week_end-1))) \
            .values("year", "week") \
            .annotate(
            historySalesCYLW=Sum(
                Case(When(sold_units=0, then=0), default='sold_units')),
        ).order_by(
            -F('week')
        )

        historyWeeklyCY = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year) & Q(week__range=(week_start, week_end))) \
            .values("year", "week") \
            .annotate(
            historySalesCY=Sum(
                Case(When(sold_units=None, then=0),
                     default='sold_units')),
            target=Sum('sold_units') * 1.2,
        ).order_by(
            -F('week')
        )

        historyWeeklyLY = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year-1) & Q(week__range=(week_start, week_end))) \
            .values("year", "week") \
            .annotate(
            historySalesLY=Sum(
                Case(When(sold_units=None, then=0),
                     default='sold_units'))
        ).order_by(
            -F('week')
        )

        df = pd.DataFrame(historyLastWeek)
        df2 = pd.DataFrame(historyWeeklyLY)
        df3 = pd.DataFrame(historyWeeklyCY)
        joinedcy = df2.join(df, rsuffix="_max")
        joined = df3.join(joinedcy, rsuffix="_min")
        joined["growthRateYearly"] = 100 * \
            (joined["historySalesCY"] - joined["historySalesLY"]) / \
            joined["historySalesLY"]
        joined["achievementRate"] = 100 * \
            (1.2 * (joined["historySalesCY"] / joined["historySalesCYLW"]))
        joined.loc[joined['historySalesCYLW'] == 0, 'achievementRate'] = 0
        del joined["week_max"], joined["year_max"], joined["week_min"], joined["year_min"]
        joined = joined.fillna(0)
        response = joined.to_dict('records')

        return Response(response)


@ swagger_auto_schema(method="GET", manual_parameters=manual_params)
@ api_view(['GET'])
def filters(request, origin):
    """
    Get filtering updated data based on already selected ids. <br> Origin: table from to start looking up; its either: <b>weeklysales</b> (sales data)
    Used to be <b> /getAllFilters </b>
    """
    if not origin in ["weeklysales"]:
        return JsonResponse({"detail": f"{origin} is not a valid origin"}, status=400)
    if origin == "weeklysales":
        queries = request.read_permissions_queries["from_weekly_sales"]
        adapter = {
            "site_id__account": "account",
            "site_id__city": "city",
            "site_id__zone": "zone",
            "site_id__region": "region",
            "site_id__country": "country",
            "product__division": "division",
            "product__group": "group",
        }
    logging.info(f"[filters] fetching product-store relationships")

    df = pd.DataFrame(WeeklySale.objects.filter(queries & Q(year=2022)).values(
        "site_id", "product").annotate(x=Count("site_id"))).drop(columns=["x"])

    logging.info(f"[filters] fetching extra data")
    products = pd.DataFrame(Product.objects.all().values(
        "id", "group", "group__value", "division", "division__value"))
    pos = pd.DataFrame(PointOfSale.objects.all().values("id", "city", "city__name", "account", "account__name", "zone", "zone__name",
                       "region", "region__name", "country", "country__name"))
    joined = df.set_index("product").join(products.set_index(
        "id")).reset_index().set_index("site_id").join(pos.set_index("id"))

    filters = list()
    for query in request.filters.children:
        values = list()
        if type(query) == Q:
            for subquery in query.children:
                field, value = subquery
                values.append(int(value))
        elif type(query) == tuple:
            field, value = query
            values.append(int(value))

        filters.append(f"{adapter[field]} in {values}")
    if len(filters):
        joined = joined.query(" & ".join(filters))

    countries = joined[["country", "country__name"]].rename(
        columns={"country": "id", "country__name": "value"}).drop_duplicates().to_dict("records")
    accounts = joined[["account", "account__name"]].rename(
        columns={"account": "id", "account__name": "value"}).drop_duplicates().to_dict("records")
    product_groups = joined[["group", "group__value"]].rename(
        columns={"group": "id", "group__value": "value"}).drop_duplicates().to_dict("records")
    divisions = joined[["division", "division__value"]].rename(
        columns={"division": "id", "division__value": "value"}).drop_duplicates().to_dict("records")
    regions = joined[["region", "region__name"]].rename(
        columns={"region": "id", "region__name": "value"}).drop_duplicates().to_dict("records")
    cities = joined[["city", "city__name"]].rename(
        columns={"city": "id", "city__name": "value"}).drop_duplicates().to_dict("records")
    country_zones = joined[["zone", "zone__name"]].rename(
        columns={"zone": "id", "zone__name": "value"}).drop_duplicates().to_dict("records")

    return Response({
        "product_groups":  product_groups,
        "divisions":  divisions,
        "regions":  regions,
        "countries":  countries,
        "accounts":  accounts,
        "cities": cities,
        "country_zones": country_zones
    })


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def dead_inventory(request):
    """
    get all dead inventory data
    """
    # first get dead inventory existing in a certain POS and which product, filter by stdev and then get weekly data based on population

    data = list()
    threads = list()
    for week in range(181-12, 181+1):

        thread = Thread(target=get_sales_data2, args=(request.filters, week, ("inventory",
                        "sold_units", "site_id", "product", "week_object"), request.user_read_permissions))
        threads.append(thread)
        thread.start()

    for thread in threads:
        data.append(thread.join())

    logging.info(f"[DEADINVENTORY] concatenating lists")
    df = pd.concat([pd.DataFrame(x) for x in data])

    logging.info(f"[DEADINVENTORY] computing stdev")
    std = df.groupby(["site_id", "product"])["inventory"].aggregate(["std"])
    std = std.rename(
        columns={"std": "standard_deviation"})

    df = df.set_index(["site_id", "product"]).join(std)

    logging.info(f"[DEADINVENTORY] fetching extra weeks")
    pos_data = pd.DataFrame(PointOfSale.objects.values("id", "gscn_site_name", "account__name")).rename(columns={
        "id": "site_id__id", "gscn_site_name": "site_id__gscn_site_name", "account__name": "site_id__account__name"})

    product_data = pd.DataFrame(Product.objects.values("id", "sku", "division__value", "group__value")).rename(columns={
        "id": "product__id", "sku": "product_sku", "division__value": "product__division__value", "group__value": "product__group__value"})

    logging.info(f"[DEADINVENTORY] joining extra data")
    joined = df.reset_index().set_index("product").join(product_data.set_index("product__id")).reset_index().rename(columns={
        "index": "product"}).set_index("site_id").join(pos_data.set_index("site_id__id")).reset_index().rename(columns={"index": "site_id__id"})

    logging.info(f"[DEADINVENTORY] joining extra data")
    joined = joined.drop(columns=["site_id__id", "product"])

    response = joined.reset_index().drop(columns=["index"]).rename(columns={
        "site_id__account__name": "account",
        "site_id__gscn_site_name": "site_name",
        "product__division__value": "division",
        "product__group__value": "product_group",
        "sold_units": "sell_out"}).to_dict('records')

    return Response(response)


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def maxweek_data(request):
    """
    get current week and last upload week in database.
    """
    print('inside maxweek_data')
    currentDate = datetime.now()
    year, week_num, day_of_week = currentDate.isocalendar()
    filters = request.read_permissions_queries["from_weekly_sales"] & request.filters
    ormResponse = WeeklySale.objects.filter(filters)\
        .values("year", "week")\
        .annotate(
        maxWeekUploaded=Max("week"),
        currentWeek=Value(week_num)
    ).order_by("-year", "-maxWeekUploaded")[0]

    return Response(ormResponse)

# @swagger_auto_schema(method="GET", manual_parameters=manual_params)


def get_flooring_plan(query, week, fields=None):
    logging.info(f"[THREAD] fetching flooring plan {week}")

    d = Flooring.objects.filter(query & Q(week=week)) if fields == None else Flooring.objects.filter(
        query & Q(week=week)).values(*fields)  # , many=True)
    d = list(d)
    logging.info(f"[THREAD] fetched flooring plan {week}")
    return d


def get_flooring_plan_request(request):
    logging.info(f"[FLOORING] Setting up query")

    plan_by_week = Flooring.objects.filter(
        request.read_permissions_queries["from_flooring"] & request.filters_from_flooring).values("week", "product__division__value", "product__product_range__value", "product__group__value", "point_of_sale__account__name").annotate(sum=Sum('target'))

    logging.info(f"[FLOORING] Returning response")
    response = normalize_fields_from_list(list(plan_by_week), {
        "product__division__value": "product_division",
        "product__group__value": "product_group",
        "point_of_sale__account__name": "account",
        "product__product_range__value": "product_range"
    })
    return response


@api_view(['GET'])
def flooring_plan(request):
    """
    get sum of flooring targets by week
    """

    response = get_flooring_plan_request(request)
    return Response(response)


def get_flooring(request):
    data = list()
    flooring = list()
    week_threads = list()
    flooring_threads = list()
    for week in range(181-12, 181+1):

        thread = Thread(target=get_sales_data2, args=(request.filters, week, (
            "week_object",
            "site_id__account__name",
            "site_id",
            "product",
            "product__group__value",
            "product__division__value",
            "product__product_range__value",
            "inventory",
            "sold_units"),
            request.user_read_permissions))
        week_threads.append(thread)
        thread.start()

    for week in range(181-12, 181+1):
        fthread = Thread(target=get_flooring_plan, args=(
            request.read_permissions_queries["from_flooring"] & request.filters_from_flooring & Q(target__gt=0), week, (
                "week",
                "product",
                "point_of_sale",
                "target")))
        flooring_threads.append(fthread)
        fthread.start()

    for thread in week_threads:
        data.append(thread.join())

    for thread in flooring_threads:
        flooring.append(thread.join())

    sales_data = pd.concat([pd.DataFrame(x) for x in data])
    flooring_data = pd.concat([pd.DataFrame(x) for x in flooring])

    #logging.info(f"[FLOORING] Fetching Flooring plan")
    # flooring_data = pd.DataFrame(FlooringSerializer(
    #    Flooring.objects.filter(Q(target__gt=0)), many=True).data)

    logging.info(f"[FLOORING] Joining sales data with flooring plan")
    joined = flooring_data.set_index(["week", "product", "point_of_sale"]).join(sales_data.rename(
        columns={"week_object": "week", "site_id": "point_of_sale"}).set_index(["week", "point_of_sale", "product"]))
    response = joined[joined["inventory"] > 0].reset_index().to_dict("records")
    response = normalize_fields_from_list(response, {
        "site_id__account__name": "account",
        "product__group__value": "product_group",
        "product__division__value": "product_division",
        "product__product_range__value": "product_range",

    })
    return response
# @swagger_auto_schema(method="GET", manual_parameters=manual_params)


@api_view(['GET'])
def flooring(request):
    """
    get current week and last upload week in database.
    """

    response = get_flooring(request)

    logging.info(f"[FLOORING] Returning response")
    return Response(response)


@api_view(['GET'])
def range_metrics_flooring(request):
    flooring = get_flooring(request)
    plan = get_flooring_plan_request(request)
    df = pd.DataFrame(flooring)
    df_plan = pd.DataFrame(plan)
    df.loc[df['inventory'] > 0, 'inventory'] = 1
    sum_inv = df.groupby(["product_range"])[["sold_units", "inventory"]].sum()
    sum_inv["plan"] = df_plan.groupby("product_range")["sum"].sum()
    sum_inv["flooring_pct"] = (100*sum_inv["inventory"])/sum_inv["plan"]
    sum_inv["run_rate"] = (sum_inv["inventory"])/sum_inv["sold_units"]

    sum_inv.replace([np.inf, -np.inf], 0, inplace=True)
    response = sum_inv.reset_index().to_dict("records")
    return Response(response)


@api_view(['GET'])
def wos(request, group):
    """
    get WoS for specified group of items. Available options are: <ul><li>/pointOfSale</li><li>/week</li></ul>
    """

    groups = {
        "pointOfSale": "site_id",
        "week": "week_object"
    }
    if not group in groups:

        return JsonResponse({
            "status": "value error",
            "detail": f"Invalid group '{group}'. Valid options are: {', '.join([x for x in groups])}"
        }, status=400)
    groupby = groups[group]

    logging.info(f"[WOS] Fetching sales data")

    data = list()
    threads = list()
    for week in range(168, 181+1):

        thread = Thread(target=get_sales_data2, args=(request.filters, week, (
            "inventory",
            "week_object",
            "sold_units",
            groupby),
            request.user_read_permissions))
        threads.append(thread)
        thread.start()

    for thread in threads:
        data.append(thread.join())

    # sales_data = WeeklySaleSimpleSerializer(
    #    WeeklySale.objects.filter(Q()), many=True).data

    logging.info(f"[WOS] Pandas process")
    #df_sales = pd.DataFrame(sales_data)
    df_sales = pd.concat([pd.DataFrame(x) for x in data])
    max_weeks = df_sales.groupby(groupby)["week_object"].max().to_frame()
    df = df_sales.join(max_weeks, on=groupby, rsuffix="_max")
    df["is_between_4w_range"] = (df["week_object"] <= df["week_object_max"]) & (
        df["week_object"] >= df["week_object_max"]-4)
    df = df[df["is_between_4w_range"]]
    sum_inventory = df.groupby(groupby)["inventory"].sum().to_frame()

    sum_so_by_group = df.groupby(list(set([groupby, "week_object_max", "week_object"])))[
        "sold_units"].sum().to_frame()
    avg_so_by_group = sum_so_by_group.reset_index().groupby(
        groupby)["sold_units"].mean().to_frame()

    joined = sum_inventory.join(avg_so_by_group).reset_index()
    joined["wos"] = joined["inventory"] / joined["sold_units"]
    joined["wos"].round(decimals=1)
    joined.loc[joined['sold_units'] == 0, 'wos'] = 0
    logging.info(f"[WOS] Returning response")

    response = joined.to_dict("records")
    return Response(list(response))


@api_view(['GET'])
def eop(request):
    """
    get WoS for specified group of items. Available options are: <ul><li>/pointOfSale</li></ul>
    """

    eop_count = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(week_object__gte=168)).values(
        "product").annotate(eop=Count("product", filter=Q(product__end_of_production__gte=date(year=1900, month=1, day=1)))).values("product", "eop")
    response = eop_count.aggregate(is_eop=Count("eop", filter=Q(
        eop__gt=0)), is_not_eop=Count("eop", filter=Q(eop=0)))
    return Response(response)


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def runratemetrics(request):
    """
    get inventory and sellouts for product range.
    """
    year = datetime.now().year
    week_start = int(request.GET.get('week_start', 25-12))
    week_end = int(request.GET.get('week_end', 25))
    logging.info(
        f"[RANGEMETRICS] getting inventory and sales {week_start}-{week_end}")

    ormResponse = WeeklySale.objects.filter(request.read_permissions_queries["from_weekly_sales"] & request.filters & Q(year=year) & Q(week__range=(week_start, week_end)))\
        .values("product__product_range__value")\
        .annotate(
        inventory=Sum('inventory'),
        sold_units=Sum('sold_units')
    )

    return Response(normalize_fields_from_list(list(ormResponse), {"product__product_range__value": "range"}))
