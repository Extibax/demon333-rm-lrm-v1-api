from rest_framework.response import Response
from rest_framework.decorators import api_view

# Create your views here.
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from django.http import Http404, JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.db.models import Q
from service.mso import MSO

# MODELS
from .models import PointOfSale, Account, PointOfSaleType, Segment

# SERIALIZERS
from .serializers import PointOfSaleSerializer, AccountSerializer, PointOfSaleTypeSerializer, SegmentSerializer, PointOfSaleMSOSerializer

filter_adapter = {
    "point_of_sale":"id",
    "point_of_sale_account":"account",
    "point_of_sale_country":"country",
    "point_of_sale_region":"region",
    "point_of_sale_zone":"zone",
    "point_of_sale_city":"city"
}

class PointOfSaleView(APIView):
    """
    Get all point of sale data
    """

    def get(self, request) -> Response:
        queries = []
        for k,v in request.query_params.items():
            if "point_of_sale" in k:
                queries.append(Q(**{filter_adapter[k] : v}))
        #queries.append(request.read_permissions_queries["from_point_of_sales"])
        
        queries = tuple(queries)

        pos = PointOfSale.objects.filter(
            *queries)
        serializer = PointOfSaleSerializer(pos, many=True)
        return Response(serializer.data)


class PointOfSaleByIdView(APIView):
    """
    Get point of sale by Id
    """

    def get(self, request, id: int) -> Response:
        pos = PointOfSale.objects.filter(Q(id__exact=id) 
        #& request.read_permissions_queries["from_point_of_sales"]
                                         ).get()
        serializer = PointOfSaleMSOSerializer(pos)
        return Response(serializer.data)


class AccountView(APIView):
    """
    Get all account data
    """

    def get(self, request) -> Response:
        account = Account.objects.filter(
            request.read_permissions_queries["from_accounts"])
        serializer = AccountSerializer(account, many=True)
        return Response(serializer.data)


class PointOfSaleTypeView(APIView):
    """Get all point of sale type data"""

    def get(self, request) -> Response:
        pos_type = PointOfSaleType.objects.all()
        serializer = PointOfSaleTypeSerializer(pos_type, many=True)
        return Response(serializer.data)


class SegmentView(APIView):
    """Get all segment data"""

    def get(self, request) -> Response:
        segment = Segment.objects.all()
        serializer = SegmentSerializer(segment, many=True)
        return Response(serializer.data)

class MSOView(APIView):
    """GET ALL MSO DATA
        SERVICE VALUES: 
        -SiteLocation
        -GoldenZone
        -OneSamsung
        -Samples
        -Stretch
        -Tables
        -Display
        -Tickets
    """

    def get(self, request, id, service) -> Response:
        pos_data = PointOfSale.objects.filter(Q(id__exact=id)).get()        
        mso_data = MSO.getSiteLocation(pos_data.site_id, service)
        return Response(mso_data)

@api_view(['GET'])
def search2(request):
    return Response({"name": "default"}, headers={
        "save-in-cache": True
    })


@api_view(['GET'])
def search(request, name):
    return Response({"name": name}, headers={
        "save-in-cache": True
    })
