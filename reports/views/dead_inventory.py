from api.common.helpers import normalize_fields_from_list
from service import logging
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from .docs import manual_params
import pandas as pd
from ..fetch import get_filtered_data_in_range
from service import Thread
from rest_framework.response import Response


@swagger_auto_schema(method="GET", manual_parameters=manual_params)
@api_view(['GET'])
def dead_inventoryV2(request, group):

    dead_inventory_fields = ["year", "week", "site_id_id",
                             "product_id", "week_object_id", group, "inventory", "sold_units"]
    weeks_dataframes = list()
    df = get_filtered_data_in_range(
        request.range["from"]-7, request.range["to"], request.all_filters)
    # drop unnecessary fields

    df.drop(columns=[k for k in df.keys()
            if not k in dead_inventory_fields], inplace=True)

    def compute_dead_inventory(df: pd.DataFrame, week: int) -> pd.DataFrame:
        # compute sums
        sums = df.groupby(["site_id_id", "product_id"])[
            ["sold_units", "inventory"]].sum()
        joined = sums.join(df.set_index(
            ["site_id_id", "product_id"]), lsuffix="_total")
        last_week = joined[joined["week_object_id"] == week]

        logging.info(f"[DEADINVENTORYV2] finished week {week}")
        return last_week

    threads = list()
    for week in range(request.range["from"], request.range["to"]+1):
        # for each week to get DI, fetch its 8 previous week for computing
        logging.info(f"[DEADINVENTORYV2] computing week {week}")
        eight_week_span_data = df[(
            df["week_object_id"] >= week-7) & (df["week_object_id"] <= week)]

        threads.append(Thread(target=compute_dead_inventory,
                       args=(eight_week_span_data, week)))
        threads[-1].start()

    for thread in threads:
        weeks_dataframes.append(thread.join())

    df = pd.concat(weeks_dataframes)
    df["is_dead"] = df["sold_units_total"] == 0
    df.reset_index(inplace=True)

    response = df.groupby([group, "is_dead", "year", "week"])[
        "inventory"].sum().reset_index().to_dict("records")

    return Response(normalize_fields_from_list(response, {
        group: "group"
    }), headers={
        "from": request.range["from"],
        "to": request.range["to"]
    })
