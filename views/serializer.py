from rest_framework import serializers
from .models import View


class ViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = View
        fields = (
            "id",
            "name",
        )
