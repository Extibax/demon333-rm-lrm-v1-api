

from rest_framework.views import APIView
from rest_framework.response import Response
from api.common.helpers import normalize_fields_from_list
from drf_yasg.utils import swagger_auto_schema
import pandas as pd
import numpy as np


from service import Thread
from .docs import manual_params
from service import logging

from ..fetch import get_filtered_data_in_range

import re
class DashboardDataView(APIView):
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

        columns = list()
        df1 = get_filtered_data_in_range(
            request.range["first_week_of_year"]-52, request.range["to"]-52, request.all_filters)
        df2 = get_filtered_data_in_range(
            request.range["first_week_of_year"], request.range["to"], request.all_filters)
        df = pd.concat([df1, df2])
       
        del df1
        del df2

        logging.info(f"[REPORTS {group}] computing sums")
        # current year sell out
        cy_so = df[(df["year"] == df["year"].max())].groupby(
            groups)["sold_units"].sum()
        cy_so.name = "cy_so"
        columns.append(cy_so)

        # last year sell out
        ly_so = df[(
            df["year"] == df["year"].max()-1)].groupby(groups)["sold_units"].sum()
        ly_so.name = "ly_so"
        columns.append(ly_so)

        # last week sell out
        cw_so = df[df["week_object_id"] == df["week_object_id"].max()].groupby(groups)[
            "sold_units"].sum()
        cw_so.name = "cw_so"
        columns.append(cw_so)

        # 2 weeks ago sell out
        lw_so = df[df["week_object_id"] == df["week_object_id"].max(
        )-1].groupby(groups)["sold_units"].sum()
        lw_so.name = "lw_so"
        columns.append(lw_so)

        # last week available inventory
        lw_inv = df[df["week_object_id"] == df["week_object_id"].max()].groupby(groups)[
            "inventory"].sum()
        lw_inv.name = "lw_inv"
        columns.append(lw_inv)
        # last week from last year sell out
        # lylw_so = df[(df["week"] == df["week"].max()) & (
        #    df["year"] == df["year"].max()-1)].groupby(groups)["sold_units"].sum()
        #lylw_so.name = "lylw_so"
        # columns.append(lylw_so)
        del df
        report = pd.concat(columns, axis=1)

        del columns
        del cy_so
        del ly_so
        del cw_so
        del lw_so
        del lw_inv

        logging.info(f"[REPORTS {group}] computing rates")
        # year on year growth rate
        report["yoy_gr_pct"] = 100 * \
            (report["cy_so"] - report["ly_so"])/report["ly_so"]
        # week on week growth rate
        report["wow_gr_pct"] = 100 * \
            (report["cw_so"] - report["lw_so"])/report["lw_so"]

        logging.info(f"[REPORTS {group}] computing portions")
        # portions
        report["ytd_pct"] = 100*report["cy_so"] / report["cy_so"].sum()
        report["lw_pct"] = 100*report["cw_so"] / report["cw_so"].sum() # current week's SO portion

        report = report.fillna(0)
        report = report.replace([np.inf, -np.inf], 0)

        if request.query_params.get("ranking", False):

            logging.info(f"[REPORTS {group}] computing ranking")
            report = report.sort_values("cw_so", ascending=False)

            best = report.iloc[:10]
            best["ytd_pct"] = 100*best["cy_so"] / best["cy_so"].sum()
            best["lw_pct"] = 100*best["cw_so"] / best["cw_so"].sum()
            best = best.fillna(0)
            best = best.replace([np.inf, -np.inf], 0)
            best = best.reset_index().to_dict("records")
            worst = report.iloc[-10:]
            worst["ytd_pct"] = 100*worst["cy_so"] / worst["cy_so"].sum()
            worst["lw_pct"] = 100*worst["cw_so"] / worst["cw_so"].sum()
            worst = worst.fillna(0)
            worst = worst.replace([np.inf, -np.inf], 0)
            worst = worst.reset_index().to_dict("records")
            
            del report
            
            return Response({
                "best": best,
                "worst": worst,

            }, headers={
                "from": request.range["first_week_of_year"],
                "to": request.range["to"],
                "sum": True
            })

        logging.info(f"[REPORTS {group}] computing response")
        #response = report.reset_index().to_dict("records")
        #del report
        
        return Response(
            report.reset_index()
            #normalize_fields_from_list(response, {group: "group"})
            , headers={
            "from": request.range["first_week_of_year"],
            "to": request.range["to"],
            "sum": True,
            "groups": ",".join(groups)
        })
