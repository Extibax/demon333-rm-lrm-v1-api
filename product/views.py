

# Create your views here.
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema


from rest_framework.views import APIView

from django.db.models import Q


# MODELS
from .models import Brand, Group, Product, Division, ProductType, Range, Segment, Week, WeeklySale

# SERIALIZERS
from .serializers import BrandSerializer, GroupSerializer, ProductSegmentSerializer, ProductSerializer, DivisionSerializer, ProductTypeSerializer, RangeSerializer, WeekSerializer

from rest_framework.decorators import api_view


class DivisionView(APIView):
    """
    Get all divisions data
    """

    def get(self, request) -> Response:
        division = Division.objects.filter(
            request.read_permissions_queries["from_divisions"])
        serializer = DivisionSerializer(division, many=True)
        return Response(serializer.data)


class BrandView(APIView):
    ''' Get all brands data '''

    def get(self, request) -> Response:
        brand = Brand.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = BrandSerializer(brand, many=True)
        return Response(serializer.data)


class GroupView(APIView):
    ''' Get all groups data '''

    def get(self, request) -> Response:
        group = Group.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = GroupSerializer(group, many=True)
        return Response(serializer.data)


class RangeView(APIView):
    ''' Get all ranges data '''

    def get(self, request) -> Response:
        range = Range.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = RangeSerializer(range, many=True)
        return Response(serializer.data)


class SegmentView(APIView):
    ''' Get all segments data '''

    def get(self, request) -> Response:
        segment = Segment.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = ProductSegmentSerializer(segment, many=True)
        return Response(serializer.data)


class ProductTypeView(APIView):
    """Get all products type data"""

    def get(self, request) -> Response:
        product_type = ProductType.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = ProductTypeSerializer(product_type, many=True)
        return Response(serializer.data)


class ProductView(APIView):
    """
    Product service without specific Id
    """

    def get(self, request) -> Response:
        product = Product.objects.filter(
            request.read_permissions_queries["from_products"])
        serializer = ProductSerializer(product, many=True)
        return Response(serializer.data)


class ProductViewId(APIView):
    """
    Product service with specific Id
    """

    def get(self, request, id: int) -> Response:
        product = Product.objects.filter(
            Q(id__exact=id) & request.read_permissions_queries["from_products"]).get()
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    # def delete(self, request, id: int) -> Response:
    #     product = Product.objects.filter(id=id).get()
    #     serializer = ProductSerializer(product)
    #     Product.objects.filter(id=id).delete()
    #     return Response(serializer.data, status=204)

    # @swagger_auto_schema(request_body=ProductSerializer)
    # def patch(self, request, id: int) -> Response:
    #     #crear un helper para cada actualizacion especifica.
    #     # brand = Brand.objects.filter(**request.data['brand']).get()
    #     # request.data['brand'] = brand
    #     product = Product.objects.filter(Q(id__exact=id) & request.read_permissions_queries["from_products"])
    #     product.update(**request.data)
    #     serializer = ProductSerializer(product.get())
    #     return Response(serializer.data, status=201)


@api_view(['GET'])
def weeks(request):
    return Response(WeekSerializer(Week.objects.all(), many=True).data)
