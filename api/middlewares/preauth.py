#from rest_framework.response import Response
from service import logging
from django.http import JsonResponse

from administration.models import User
from administration.serializers import RoleSerializer
from hashlib import md5
from api.settings import CACHE_URL_NAMES
from api.settings import elastic_cache
from api.settings import SECRET_KEY

from datetime import datetime

from administration.errors import LRMAuthenticationException
from api.middlewares.exceptions import ExceptionHandlerMiddleware
#from django.http.request import HttpRequest
import jwt
import json


class PreauthenticationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Code that is executed in each request before the view is called

        response = self.get_response(request)

        # Code that is executed in each request after the view is called
        return response

    
    def process_view(self, request, view_func, view_args, view_kwargs):

        try:
            # try to get the user from token
            token = request.headers["Authorization"].replace("Bearer ", "")
            token_data = jwt.decode(token, SECRET_KEY, algorithms=[
                              "HS256"])
        except Exception as ex:

            logging.info(
                f"[CACHE MIDDLEWARE] Could not retrieve user or token data. {ex}")
            return
        
        token_day =datetime.fromtimestamp(token_data["exp"]).day
        today =datetime.now().day

        
        try:
            
            if token_day == today:
                raise LRMAuthenticationException("Token expired")
        except LRMAuthenticationException as exception:

            return JsonResponse({
                "detail": f"{exception}",
                #"params": "Token expired"
            }, status=401)


    