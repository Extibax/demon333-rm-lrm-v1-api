

from rest_framework.views import APIView
from rest_framework.response import Response
from api.common.helpers import normalize_fields_from_list
from drf_yasg.utils import swagger_auto_schema

from .docs import manual_params
from service import logging

from ..fetch import get_filtered_data_in_range

import re


class InventoryMetricsView(APIView):
    """
    Get dashboard data by group. use ranking=true for getting ordered data based on current week sell out
    """
    @swagger_auto_schema(manual_parameters=manual_params)
    def get(self, request, group: str) -> Response:

        compound_groups = re.findall("groups:(.+)", group)
        if compound_groups:
            groups = compound_groups[0].split("$")
        else:
            groups = [group]
        df = get_filtered_data_in_range(
            request.range["from"]-1, request.range["to"], request.all_filters)

        logging.info(f"[INVENTORY METRICS {group}] computing sums")
        

        return Response(df, headers={
            "from": request.range["from"]-1,
            "to": request.range["to"],
            "groups": ",".join(groups),
            "sum_fields": ",".join(["inventory", "sold_units"])
        })
        sums = df.groupby(groups)[["inventory", "sold_units"]].sum(
        ).reset_index().to_dict("records")

        return Response(normalize_fields_from_list(sums, {
            group: "group"
        }), headers={
            "from": request.range["from"],
            "to": request.range["to"]
        })
