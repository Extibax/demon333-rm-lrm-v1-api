
import hashlib
import json
from locale import normalize
import os
from django.http import JsonResponse
from more_itertools import powerset
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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import pandas as pd
import numpy as np
from service import logging
from product.models import Product, WeeklySale
from product.models import Group
from product.models import Division
from locations.models import Region
from locations.models import Country
from store.models import Account, PointOfSale

from sklearn.linear_model import LinearRegression
# from product.serializers import WeeklySaleSerializer

from product.serializers import WeeklySaleSimpleSerializer
from reports.models import Flooring
from reports.serializers import FlooringSerializer
from api.common.helpers import normalize_fields_from_list
from service import Thread
from .docs import manual_params
from hashlib import md5
from service.storage_cache import StorageCache
from api.settings import elastic_cache
from ..fetch import get_filtered_data_in_range
from ..fetch import adapter
from django.http import HttpRequest
from api.settings import s3
import re


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

    product_fields = ("id", "group", "group__value",
                      "division", "division__value")
    pos_fields = ("id", "city", "city__name", "account", "account__name", "zone", "zone__name",
                  "region", "region__name", "country", "country__name")

    products = pd.DataFrame(Product.objects.all().values(*product_fields))
    pos = pd.DataFrame(PointOfSale.objects.all().values(*pos_fields))

    df = pd.DataFrame(d)
    joined = df.set_index("product").join(products.set_index(
        "id")).reset_index().rename(columns={"index": "product"}).set_index("site_id").join(pos.set_index("id")).reset_index().rename(columns={"index": "site_id"})

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

        report = report.fillna(0)
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


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def run_rate(request, group):
    compound_groups = re.findall("groups:(.+)", group)
    if compound_groups:
        groups = compound_groups[0].split("$")

    else:
        groups = [group]

    df = get_filtered_data_in_range(
        request.range["from"]-3, request.range["to"], request.all_filters, flooring=True)

    if len(df) != 0:
        df.loc[df["inventory"] == 0, "in_place"] = 0
        df.loc[df["inventory"] > 0, "in_place"] = 1

        sums = ["inventory", "in_place", "sold_units"]

        df = df.groupby(groups)[sums].sum().reset_index()

        df["run_rate"] = df['sold_units'] / df['in_place']
        agg = dict(zip(sums, ['sum']*len(sums)))

        #week_absolute_range = request.range["to"] -request.range["from"]-3
        # df.week.drop_duplicates()[-week_absolute_range:]

        weeks = [x for x in df.week.drop_duplicates() if x >=
                 df["week"].min() + 3]

        dfs = pd.DataFrame()

        for w in weeks:
            df_2 = df[(df['week'] >= w-3) & (df['week'] <= w)].groupby(
                [x for x in groups if x != 'week']).agg({'run_rate': 'mean', **agg}).reset_index()
            df_2['week'] = w
            print(df_2)
            # agregar df_2 a dfs
            dfs = dfs.append(df_2, ignore_index=True)

        reports = dfs

        # delete runrate Nan
        reports = reports.fillna(0.0)
        reports = reports.replace([np.inf, -np.inf], 0)
    else:
        reports = pd.DataFrame([])

    return Response(reports.to_dict("records"), headers={"from": request.range["from"]-3,
                                                         "to": request.range["to"]})


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

    joined = get_filtered_data_in_range(
        request.range["first_week_of_year"], request.range["to"], request.all_filters)
    joined = joined.fillna(0)

    if len(joined) != 0:
        joined = joined.replace([np.inf, -np.inf], 0)
        countries = joined[["country", "country__name"]].rename(
            columns={"country": "id", "country__name": "value"}).drop_duplicates().to_dict("records")
        accounts = joined[["custom_account", "custom_account__name"]].rename(
            columns={"custom_account": "id", "custom_account__name": "value"}).drop_duplicates().to_dict("records")
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
        ranges = joined[["product_range", "product_range__value"]].rename(
            columns={"product_range": "id", "product_range__value": "value"}).drop_duplicates().to_dict("records")
        point_of_sales = joined[["site_id_id", "gscn_site_name"]].rename(
            columns={"site_id_id": "id", "gscn_site_name": "value"}).drop_duplicates().to_dict("records")

        # types
        inches = joined[joined["INCHES"] != 0]["INCHES"].to_frame()
        inches = inches.rename(columns={"INCHES": "value"})
        inches["id"] = inches["value"]
        inches = inches.drop_duplicates().to_dict("records")

        loads = joined[joined["LOAD"] != 0]["LOAD"].to_frame()
        loads = loads.rename(columns={"LOAD": "value"})
        loads["id"] = loads["value"]
        loads = loads.drop_duplicates().to_dict("records")
    else:
        return Response({
            "product_groups": [],
            "divisions": [],
            "regions": [],
            "countries": [],
            "accounts": [],
            "cities": [],
            "country_zones": [],
            "point_of_sales": [],
            "ranges": [],

            # product types
            "inches": [],
            "loads": [],
        })

    return Response({
        "product_groups":  product_groups,
        "divisions":  divisions,
        "regions":  regions,
        "countries":  countries,
        "accounts":  accounts,
        "cities": cities,
        "country_zones": country_zones,
        "point_of_sales": point_of_sales,
        "ranges": ranges,

        # product types
        "inches": inches,
        "loads": loads,
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

    return Response(request.range)

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


@api_view(['GET'])
@permission_classes([AllowAny])
def combinations(request):
    """
    get all available combinations
    """
    # group  division  product_range  account  country
    banned_fields = ["LOAD", "INCHES", "site_id_id",
                     "zone", "city", "region", "segment"]
    weeks_dataframes = list()
    df = get_filtered_data_in_range(
        request.range["from"]-7, request.range["to"], request.all_filters)
    # drop unnecessary fields

    fields = [k for k in adapter if k not in banned_fields]

    # population 1
    df1 = df.drop(columns=[k for k in df.keys()
                           if not k in fields])
    df1 = df1.drop_duplicates()
    product = df1.astype("int64").to_dict("tight")["data"]

    # banned_fields_2 = ["LOAD", "INCHES", "zone",
    #                    "city", "region", "account", "country"]
    # fields2 = [k for k in adapter if k not in banned_fields_2]
    # df2 = df.drop(columns=[k for k in df.keys()
    #                        if not k in fields2])
    # df2 = df2.drop_duplicates()
    # product2 = df2.astype("int64").to_dict("tight")["data"]

    combinations = set()

    keys = {
        "group": "product_group",
        "division": "product_division",
        "account": "point_of_sale_account"
    }

    for p in product:

        for k in range(len(df1.keys())):

            p[k] = f"{adapter[df1.keys()[k]]}={p[k]}"

        for item in powerset(p):
            combinations.add("&".join(item))

    def product_group_rule(x): return True if "product_group" in x and "product_division" in x else (
        True if not "product_group" in x else False)
    def account_rule(x): return True if "point_of_sale_country" in x and "point_of_sale_account" in x else (
        True if not "point_of_sale_account" in x else False)

    combinations = [c for c in combinations if product_group_rule(
        c) and account_rule(c)]

    return Response(combinations)


def sha256(fichero):
    fp = open(fichero, "rb")
    buffer = fp.read()
    # sha256
    hashObj = hashlib.sha256()
    hashObj.update(buffer)
    lastHash = hashObj.hexdigest().upper()
    sha256 = lastHash
    fp.close()
    return fichero, sha256


@api_view(['POST'])
def excel_reports(request):
    """
    resive a request and send an excel report
    """
    df = pd.DataFrame(request.data['rows'])
    df = df.rename(request.data['columns'], axis=1)

    df.index = df.index + 1
    if (request.data['type'] == 'xlsx'):
        df.to_excel("output.xlsx", index=False)
        # se genera el hash del fichero
        old, new = sha256("output.xlsx")
        new = f'{new}.xlsx'

    if (request.data['type'] == 'csv'):
        df.to_csv('output.csv', index=False)
        old, new = sha256("output.csv")
        new = f'{new}.csv'
    # se cambia el nombre del fichero
    os.rename(old, new)

    # se sube a la nube el fichero
    s3_bucket_name = 'local-retail-management-assets'
    key_name = 'downloaded_reports/'+new

    with open(new, 'rb') as data:
        s3.upload_fileobj(data, s3_bucket_name, key_name)

    res = s3.generate_presigned_url(
        "get_object", Params={'Bucket': s3_bucket_name, 'Key': key_name})

    # se borra el fichero local
    os.remove(new)
    return Response({"url": res})


@api_view(['POST'])
def send_linear_regression(request):
    x = np.array(request.data['x']).reshape((-1, 1))  # weeks
    y = np.array(request.data['y'])  # visits
    model = LinearRegression().fit(x, y)
    # same weeks
    y_new = model.predict(x)

    return Response(y_new)
