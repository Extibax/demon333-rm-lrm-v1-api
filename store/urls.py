from django.urls import path

from .views import PointOfSaleTypeView, SegmentView, search, PointOfSaleView, AccountView, PointOfSaleByIdView, MSOView

urlpatterns = [
    path('test', search),
    path('test/<str:name>', search, name="cachetest"),
    path('pointOfSales', PointOfSaleView.as_view()),
    path('pointOfSales/<int:id>', PointOfSaleByIdView.as_view()),
    path('account', AccountView.as_view()),
    path('pos_type', PointOfSaleTypeView.as_view()),
    path('segment', SegmentView.as_view()),
    path('mso_data/<str:service>/<str:id>', MSOView.as_view()),
]
