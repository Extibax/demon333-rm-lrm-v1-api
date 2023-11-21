from api.common.helpers import normalize_fields_from_list
from service import logging
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from .docs import manual_params
import pandas as pd
from ..fetch import get_filtered_data_in_range
from service import Thread
from rest_framework.response import Response
import re


@api_view(['GET'])
def l2_generator(request):

    df = get_filtered_data_in_range(
        request.range["first_week_of_year"], request.range["to"], request.all_filters, flooring=True)
    del df
    return Response({
        "status": True
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
