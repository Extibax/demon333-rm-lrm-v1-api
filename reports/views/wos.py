from service import logging
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
import pandas as pd
from ..fetch import get_filtered_data_in_range
from rest_framework.response import Response

@api_view(['GET'])
def wosv2(request, group):
    """
    get WoS for specified group of items. Available options are: <ul><li>/site_id</li><li>/week</li></ul>
    """

    df = get_filtered_data_in_range(
        request.range["from"], request.range["to"], request.all_filters)

    logging.info(f"[WOS] Pandas process")

    max_weeks = df.groupby(group)["week_object_id"].max().to_frame()
    df = df.join(max_weeks, on=group, rsuffix="_max")
    df["is_between_4w_range"] = (df["week_object_id"] <= df["week_object_id_max"]) & (
        df["week_object_id"] >= df["week_object_id_max"]-4)
    df = df[df["is_between_4w_range"]]
    sum_inventory = df.groupby(group)["inventory"].sum().to_frame()

    sum_so_by_group = df.groupby(list(set([group, "week_object_id_max", "week_object_id"])))[
        "sold_units"].sum().to_frame()
    avg_so_by_group = sum_so_by_group.reset_index().groupby(
        group)["sold_units"].mean().to_frame()

    joined = sum_inventory.join(avg_so_by_group).reset_index()
    joined["wos"] = joined["inventory"] / joined["sold_units"]
    joined["wos"].round(decimals=1)
    joined.loc[joined['sold_units'] == 0, 'wos'] = 0
    logging.info(f"[WOS] Returning response")

    response = joined.to_dict("records")
    return Response(list(response))
