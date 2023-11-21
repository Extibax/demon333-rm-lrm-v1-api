
from views.models import View
from views.serializer import ViewSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.

class ViewsView(APIView):
    def get(self, request) -> Response:
        """
        Get all views
        """
        views = View.objects.all()
        serializer = ViewSerializer(views, many=True)
        return Response(serializer.data)
