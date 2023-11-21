from django.urls import path

from product.serializers import ProductTypeSerializer
from .views import BrandView, GroupView, ProductTypeView, ProductView, ProductViewId, DivisionView, RangeView, SegmentView, weeks

urlpatterns = [

    path('', ProductView.as_view()),
    path('<int:id>', ProductViewId.as_view()),
    path('divisions', DivisionView.as_view()),
    path('brand', BrandView.as_view()),
    path('group', GroupView.as_view()),
    path('range', RangeView.as_view()),
    path('segment', SegmentView.as_view()),
    path('product_types', ProductTypeView.as_view()),

]
