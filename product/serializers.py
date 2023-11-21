

from rest_framework import serializers

from .models import Division, Product, Group, Brand, Range, Segment, ProductType, Week, WeeklySale


class BrandNameField(serializers.RelatedField):
    def to_representation(self, value):
        return value.value


class DivisionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Division
        fields = (
            "id",
            "value",
        )


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = (
            "id",
            "value",
        )


class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = (
            "id",
            "value",
        )


class RangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Range
        fields = (
            "id",
            "value",
        )


class ProductSegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Segment
        fields = (
            "id",
            "value",
        )


class ProductTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductType
        fields = (
            "id",
            "product",
            "key",
            "value",
        )


class ProductSerializer(serializers.ModelSerializer):
    #division = DivisionSerializer()
    #group = GroupSerializer()
    #brand = BrandSerializer(required=True)
    #product_range = RangeSerializer()
    #segment = ProductSegmentSerializer()
    #brand = BrandNameField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "marketing_name",
            "brand",
            "segment",
            "product_range",
            "division",
            "group"
        )


class WeeklySaleSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = WeeklySale
        fields = (
            "id",
            "year",
            "week",
            "first_date_of_week",
            "site_id",
            "product",
            "sold_units",
            "inventory"
        )


class WeeklySaleSimpleSerializer(serializers.ModelSerializer):
    #product = ProductSerializer()

    class Meta:
        model = WeeklySale
        fields = (
            # "id",
            # "year",
            # "week",
            "week_object",
            # "first_date_of_week",
            "site_id",
            "product",
            "sold_units",
            "inventory"
        )


class ProductGroupField(serializers.RelatedField):
    def to_representation(self, value):

        return value.product.group.value


class ProductDivisionField(serializers.RelatedField):
    def to_representation(self, value):
        return value.product.division.value


class WeeklySaleForFlooringSerializer(serializers.ModelSerializer):
    #product = ProductSerializer()
    # queryset  ? product_division = ProductDivisionField()
    #product_group = ProductGroupField()

    class Meta:
        model = WeeklySale
        fields = (
            # "id",
            # "year",
            # "week",
            "week_object",
            # "first_date_of_week",
            "product_division",
            "product_group",
            "site_id",
            "product",
            "inventory",
            "sold_units"
        )


class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = (
            "id",
            "year",
            "week"
        )
