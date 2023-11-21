from rest_framework import serializers
from .models import PointOfSale
from .models import Segment
from .models import PointOfSaleType
from .models import Account
from locations.serializers import CitySerializer, CountryZoneSerializer, CountrySerializer, RegionSerializer
#from .models import CountryGroup


class SegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Segment
        fields = (
            "id",
            "value",
        )


class PointOfSaleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PointOfSaleType
        fields = (
            "id",
            "value")


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = (
            "id",
            "name",
        )


class PointOfSaleSerializer(serializers.ModelSerializer):
    #city = CitySerializer()
    #segment = SegmentSerializer()
    #account = AccountSerializer()
    #pos_type = PointOfSaleTypeSerializer()

    class Meta:
        model = PointOfSale
        fields = (
            "id",
            "site_id",
            "gscn_site_name",
            "latitude",
            "longitude",
            "status",
            "pos_type",
            "city",
            "segment",
            "account",
        )


class PointOfSaleMSOSerializer(serializers.ModelSerializer):
    account = AccountSerializer()
    city = CitySerializer()    
    # pos_type = PointOfSaleTypeSerializer()
    # segment = SegmentSerializer()
    country = CountrySerializer()
    region = RegionSerializer()
    zone = CountryZoneSerializer()
    # custom_account = AccountSerializer()

    class Meta:
        model = PointOfSale
        fields = (
            "id",
            "site_id",
            "gscn_site_name",
            "status",
            "account",
            "city",
            # "pos_type",
            # "segment",
            "latitude",
            "longitude",
            "mso_name",
            "country",
            "region",
            "zone",
            # "custom_account",
        )
