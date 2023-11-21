from django.shortcuts import render

from locations.models import Country
from locations.serializers import CountrySerializer
from rest_framework.response import Response
from rest_framework.views import APIView



# Create your views here.
class CountryView(APIView):
    def get(self, request) -> Response:
        """
        Get all countries
        """
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data)
