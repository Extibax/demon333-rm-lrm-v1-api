
from api.common.helpers import normalize_fields_from_list

from service import logging


class SumMiddleware:
    """Middleware in charge on grouping responses based on group path"""

    # filter keys should have standardized names as module__model, this is for validation of params

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        sums = response.headers.get("sum")

        if not sums:
            return response

        if type(response.data) == dict and response.data.get("best") and response.data.get("worst"):
            response.data["best"] = {
                "detail": response.data["best"],
                "sum": {
                    "cy_so": sum([x["cy_so"] for x in response.data["best"]]),
                    "ly_so": sum([x["ly_so"] for x in response.data["best"]]),
                    "ytd_pct": sum([x["ytd_pct"] for x in response.data["best"]]),
                    "yoy_gr_pct": sum([x["yoy_gr_pct"] for x in response.data["best"]]),
                    "lw_so": sum([x["lw_so"] for x in response.data["best"]]),
                    "cw_so": sum([x["cw_so"] for x in response.data["best"]]),
                    "lw_pct": sum([x["lw_pct"] for x in response.data["best"]]),
                    "wow_gr_pct": sum([x["wow_gr_pct"] for x in response.data["best"]]),
                    "lw_inv": sum([x["lw_inv"] for x in response.data["best"]])
                }
            }
            response.data["worst"] = {
                "detail": response.data["worst"],
                "sum": {
                    "cy_so": sum([x["cy_so"] for x in response.data["worst"]]),
                    "ly_so": sum([x["ly_so"] for x in response.data["worst"]]),
                    "ytd_pct": sum([x["ytd_pct"] for x in response.data["worst"]]),
                    "yoy_gr_pct": sum([x["yoy_gr_pct"] for x in response.data["worst"]]),
                    "lw_so": sum([x["lw_so"] for x in response.data["worst"]]),
                    "cw_so": sum([x["cw_so"] for x in response.data["worst"]]),
                    "lw_pct": sum([x["lw_pct"] for x in response.data["worst"]]),
                    "wow_gr_pct": sum([x["wow_gr_pct"] for x in response.data["worst"]]),
                    "lw_inv": sum([x["lw_inv"] for x in response.data["worst"]])
                }
            }
            return response

        response.data = {
            "detail": response.data,
            "sum": {

                "cy_so": sum([x["cy_so"] for x in response.data]),
                "ly_so": sum([x["ly_so"] for x in response.data]),
                "ytd_pct": sum([x["ytd_pct"] for x in response.data]),
                "yoy_gr_pct": sum([x["yoy_gr_pct"] for x in response.data]),
                "cw_so": sum([x["cw_so"] for x in response.data]),
                "lw_so": sum([x["lw_so"] for x in response.data]),
                "lw_pct": sum([x["lw_pct"] for x in response.data]),
                "wow_gr_pct": sum([x["wow_gr_pct"] for x in response.data]),
                "lw_inv": sum([x["lw_inv"] for x in response.data])
            }
        }
        return response
