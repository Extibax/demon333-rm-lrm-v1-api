from rest_framework import serializers
from .models import Country
from .models import Region
from .models import CountryZone
from .models import City
from .models import CountryGroup


class CountryGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = CountryGroup
        fields = (
            "id",
            "name",
            # "countrygroup"
        )


class CountrySerializer(serializers.ModelSerializer):
    group = CountryGroupSerializer(many=True)

    class Meta:
        model = Country
        fields = (
            "id",
            "name",
            "code",
            "group",
            "longitude",
            "latitude"
        )


class RegionSerializer(serializers.ModelSerializer):
    # country = CountrySerializer()

    class Meta:
        model = Region
        fields = (
            "id",
            "name",
            # "country"
        )


class CountryZoneSerializer(serializers.ModelSerializer):
    # region = RegionSerializer()

    class Meta:
        model = CountryZone
        fields = (
            "id",
            "name",
            # "region",
        )


class CitySerializer(serializers.ModelSerializer):
    # zone = CountryZoneSerializer()

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            # "zone",
        )
