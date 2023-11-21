
from itertools import count
import json
from api.common.helpers import normalize_fields_from_list
import pandas as pd
from service import logging


def find_tuple_in_dict(dict):
    i = 0
    while i < len(dict):
        if type(list(dict.keys())[i]) == tuple:
            tuple_ = True
            break
        else:
            tuple_ = False
            i += 1
    return tuple_


def add_aggrupation_column(data, groups) -> pd.DataFrame:
    data["aggrupation"] = "$$".join(groups)
    data = data.reset_index()
    try:
        data = data.drop(columns=["index"])
    except:
        pass
    data["aggrupation"] = data[groups].apply(lambda y: (
        "$$").join([str(y[x]) for x in y.keys()]), axis=1)
    return data


class GroupingMiddleware:
    """Middleware in charge on grouping responses based on group path"""

    # filter keys should have standardized names as module__model, this is for validation of params

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        groups = response.headers.get("groups")
        if not groups:
            return response
        groups = groups.split(",")

        # si llega aggregations
        agg = response.headers.get("agg", False)
        sums = response.headers.get("sum_fields")
        if not agg and bool(sums):
            sums = response.headers.get("sum_fields", "").split(",")

            data = response.data.groupby(groups)[sums].sum()
            data = add_aggrupation_column(data, groups)

            #data["group"] = data["group"] = "$$".join(groups)
            data = data.to_dict("records")
        elif (not agg) and (not bool(sums)):

            data = add_aggrupation_column(response.data, groups)

            data["group"] = data["group"] = "$$".join(groups)
            data = data.to_dict("records")

        else:
            agg = json.loads(agg.replace("'", '"'))
            grp = response.data.groupby(groups).agg(agg).reset_index()
            grp = add_aggrupation_column(grp, groups)

            if request.qparams.get("sort_by", False):
                grp = grp.sort_values(by=request.qparams.get("sort_by"))
            records = grp.to_dict("records")

            # lo que eivar mando por discord

            tuple_in_dict = find_tuple_in_dict(records[0])

            if tuple_in_dict:
                parsed = [[{k[0] + (("_"+k[1]) if len(k[1])else ""): records[x][k]}
                           for k in records[x]] for x in range(len(records))]
                data = [{k: v for d in x for k, v in d.items()}
                        for x in parsed]

            else:
                data = records

        response.data = data
        del data

        return response
