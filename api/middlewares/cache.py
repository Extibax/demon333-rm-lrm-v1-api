#from rest_framework.response import Response
from service import logging
from django.http import JsonResponse

from administration.models import User
from administration.serializers import RoleSerializer
from hashlib import md5
from api.settings import CACHE_URL_NAMES
from api.settings import elastic_cache
from api.settings import SECRET_KEY
import copy

import jwt
import json


class ElasticCacheMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Code that is executed in each request before the view is called

        response = self.get_response(request)

        # Code that is executed in each request after the view is called
        return response

    def get_hash(self, request, userid=0):

        u = User.objects.get(id=userid)

        try:
            u.roles
        except Exception as ex:
            return None

        serializer = RoleSerializer(u.roles.all(), many=True)

        countries = set()
        point_of_sales = set()
        views = set()
        accounts = set()
        divisions = set()
        for role in serializer.data:
            for country in role["countries"]:
                countries.add(country["code"])
            #for pos in role["point_of_sales"]:
            #    point_of_sales.add(pos["gscn_site_name"])
            #for view in role["views"]:
            #    views.add(view["name"])
            for account in role["accounts"]:
                accounts.add(account["name"])
            for division in role["divisions"]:
                divisions.add(division["value"])

        countries = ",".join([str(n) for n in countries])
        #point_of_sales = ",".join([str(n) for n in point_of_sales])
        #views = ",".join([str(n) for n in views])
        accounts = ",".join([str(n) for n in accounts])
        divisions = ",".join([str(n) for n in divisions])

        #hash_content = (f"{request.get_full_path()}|{countries}|{point_of_sales}|{views}|{accounts}|{divisions}").encode("utf-8")
        hash_content = (f"{countries}|{accounts}|{divisions}").encode("utf-8")

        # request.resolver_match.kwargs

        thehash = md5(hash_content).hexdigest()
        logging.info(
            f"[CACHE MIDDLEWARE] hash for {hash_content} is {thehash}")
        return thehash

    def process_view(self, request, view_func, view_args, view_kwargs):

        try:
            # try to get the user from token
            token = request.headers["Authorization"].replace("Bearer ", "")
            user = jwt.decode(token, SECRET_KEY, algorithms=[
                              "HS256"])["user_id"]
        except Exception as ex:

            logging.info(
                f"[CACHE MIDDLEWARE] Could not retrieve user or token data. {ex}")
            return

        logging.info(
            f"[CACHE MIDDLEWARE] Url: {request.resolver_match.url_name} in {CACHE_URL_NAMES}? {request.resolver_match.url_name in CACHE_URL_NAMES}")
        if request.resolver_match.url_name in CACHE_URL_NAMES:
            logging.info(
                f"[CACHE MIDDLEWARE] {request.resolver_match.url_name} is set to be cached")
            hashed_contents = self.get_hash(request, user)
            if not hashed_contents:
                logging.info(f"[CACHE MIDDLEWARE] Unable to digest hash")
                return

            cache_key = f"{request.get_full_path()}:{hashed_contents}"

            setattr(request, "cache_key", cache_key)
            logging.info(
                f"[CACHE MIDDLEWARE] looking for cache key {request.cache_key}")

            if request.headers.get('Read-Cache', 'True') == "True":

                cache = elastic_cache.get(cache_key)
                if cache:

                    response = json.loads(cache.decode("utf-8"))
                    logging.info(f"[CACHE MIDDLEWARE] returning cached data")
                    return JsonResponse(response, safe=False, headers={
                        "cache-key": cache_key
                    })
                else:
                    logging.info(f"[CACHE MIDDLEWARE] No cache found")

        else:
            logging.info(f"[CACHE MIDDLEWARE] Set not to read cache")

        # return JsonResponse({"a": 12}, status=404)
        # This code is executed just before the view is called

    def process_template_response(self, request, response):
        
        try:
            request.cache_key
            #save_in_cache = response.headers["save-in-cache"]
        except Exception as ex:
            if str(ex) != "'WSGIRequest' object has no attribute 'cache_key'":
                logging.info(f"[CACHE MIDDLEWARE] Cache not saved. {ex}")
            response.headers["save-in-cache"] = "False"
            return response

        if not request.resolver_match.url_name in CACHE_URL_NAMES:
            logging.info(f"[CACHE MIDDLEWARE] URL not set to be cached")
            return response

        key = f"{request.cache_key}"

        logging.info(f"[CACHE MIDDLEWARE] Saving response on {key}")
        
        data_to_be_cached = json.dumps(copy.deepcopy(response.data))
        elastic_cache.set(key, data_to_be_cached)

        logging.info(f"[CACHE MIDDLEWARE] Returning response")

        if request.headers.get("is-cache-batch", False):
            response.data = {"success": True}
            response.status_code = 201
            response.headers["cache-key"] = request.cache_key
        # This code is executed if the response contains a render() method

        return response
