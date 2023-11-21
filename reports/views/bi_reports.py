from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import date
import requests
from ..models import PowerBI
from django.db.models import Q
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.decorators import api_view


# class BIReportsView(APIView):
#     """
#     Get power bi report by id
#     """
#     renderer_classes=[StaticHTMLRenderer]
#     def get(self, request, id: int) -> Response:
#         # GET TOKEN
#         url = "https://app.powerbi.com/view"
#         data = PowerBI.objects.filter(Q(id__exact=id)).get()         
#         # GET ORIGINAL HTML
#         raw_html = requests.get(f"{url}?r={data.token}").content.decode("utf-8")
#         # raw_html = urllib.request.urlopen(f"{url}?r={data.token}").read().decode("utf8")
#         # MODIFY HTML 
#         raw_html = raw_html.replace("13.0.19403.8/scripts/hash-manifest.js", "https://app.powerbi.com/13.0.19403.8/scripts/hash-manifest.js")
#         raw_html = "<p>hola</p>"
#         # raw_html = raw_html.replace("\r", "").replace("\n", "")
#         # RESPONSE 
#         return Response(raw_html, headers={"powerbi-token": data.token})


@api_view(['GET'])
# @renderer_classes([StaticHTMLRenderer])
def bireports(request, id: int) -> Response:
    # GET TOKEN
    url = "https://app.powerbi.com/view"
    data = PowerBI.objects.filter(Q(id__exact=id)).get()         
    # GET ORIGINAL HTML
    raw_html = requests.get(f"{url}?r={data.token}").content.decode("utf-8")
    # raw_html = urllib.request.urlopen(f"{url}?r={data.token}").read().decode("utf8")
    # MODIFY HTML 
    raw_html = raw_html.replace("13.0.19445.37/scripts/hash-manifest.js", "https://app.powerbi.com/13.0.19445.37/scripts/hash-manifest.js")
    f = open("file.html","w")
    f.write(raw_html)
    f.close()
    # raw_html = raw_html.replace("\r", "").replace("\n", "")
    # RESPONSE 
    return Response(raw_html, headers={"powerbi-token": data.token})