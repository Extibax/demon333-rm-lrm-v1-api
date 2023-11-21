from api.common.helpers import normalize_fields_from_list

from service import logging
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from .docs import manual_params
import pandas as pd

from service import Thread
from rest_framework.response import Response
from service.storage_cache import StorageCache
import re
from reports.models import Flooring
from django.db.models import Q
from ..fetch import get_filtered_data_in_range, get_filtered_data_in_range_fp


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def flooring(request, group):

    compound_groups = re.findall("groups:(.+)", group)
    if compound_groups:
        groups = compound_groups[0].split("$")
    else:
        groups = [group]
    flooring_fields = ["year", "week", "site_id_id",
                       "product_id", "week_object_id", "inventory", "sold_units", "flooring_plan"]+groups

    df = get_filtered_data_in_range(
        request.range["from"], request.range["to"], request.all_filters, flooring=True)

    df.drop(columns=[k for k in df.keys()
            if not k in flooring_fields], inplace=True)

    if len(df) != 0:
        df.loc[df["inventory"] == 0, "in_place"] = 0
        df.loc[df["inventory"] > 0, "in_place"] = 1
        sums = ["inventory", "in_place", "sold_units", "flooring_plan"]
    else:
        sums = ["inventory", "sold_units"]

    return Response(df, headers={
        "from": request.range["from"],
        "to": request.range["to"],
        "groups": ",".join(groups),
        "sum_fields": ",".join(sums)

    })
    report = df[df["flooring_plan"] > 0].groupby(
        groups)[["inventory", "in_place", "flooring_plan", "sold_units"]].sum()
    del df

    report["execution"] = 100*report["in_place"]/report["flooring_plan"]

    return Response(normalize_fields_from_list(report.reset_index().to_dict("records"), {
        group: "group"
    }), headers={
        "from": request.range["from"]-3,
        "to": request.range["to"],
        "group": group
    })


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def flooring_plan(request, group):
    # goup by: week_id, point_of_sale_id,product_id
    compound_groups = re.findall("groups:(.+)", group)
    if compound_groups:
        groups = compound_groups[0].split("$")
    else:
        groups = [group]

    df = get_filtered_data_in_range_fp(
        request.range["from"], request.range["to"], request.all_filters, flooring=True)

    return Response(df, headers={
        "from": request.range["from"],
        "to": request.range["to"],
        "groups": ",".join(groups),
        "sum_fields": ",".join(["flooring_plan"])
    })
