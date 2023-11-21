from django.http import JsonResponse
from product.models import Product, Division, WeeklySale
from store.models import PointOfSale, Account
from administration.models import ViewsLog, Role, User
from service.mso import MSOConnectionError
import os
import traceback


class ExceptionHandlerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):

        if type(exception) == Product.DoesNotExist:
            return JsonResponse({
                "detail": "Product does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == Division.DoesNotExist:
            return JsonResponse({
                "detail": "Division does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == PointOfSale.DoesNotExist:
            return JsonResponse({
                "detail": "Point of sale does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == Role.DoesNotExist:
            return JsonResponse({
                "detail": "Role does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == Account.DoesNotExist:
            return JsonResponse({
                "detail": "Account does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == Role.DoesNotExist:
            return JsonResponse({
                "detail": "Role does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == ViewsLog.DoesNotExist:
            return JsonResponse({
                "detail": "Action log does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == WeeklySale.DoesNotExist:
            return JsonResponse({
                "detail": "Weekly sale does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == User.DoesNotExist:
            return JsonResponse({
                "detail": "User does not exist",
                "params": request.resolver_match.kwargs
            }, status=404)
        elif type(exception) == MSOConnectionError:
            return JsonResponse({
                "detail": f"{exception}",
                "params": request.resolver_match.kwargs
            }, status=502)
        else:

            r = [x for x in dir(request) if x[0] != "_" and x != "environ"]
            req_d = dict()
            for k in r:
                if k == "body":
                    continue
                req_d[k] = str(eval(f"request.{k}"))

            return JsonResponse({
                "detail": f"{exception}",
                "params": req_d,
                "traceback": [x for x in traceback.format_exception(exception, exception, exception.__traceback__)]
            }, status=500)
