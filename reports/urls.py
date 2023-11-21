from reports.views.dashboard import DashboardDataView
from reports.views.wos import wosv2
from reports.views.dead_inventory import dead_inventoryV2
from reports.views.inventory import InventoryMetricsView
from reports.views.flooring import flooring, flooring_plan
from reports.views.bi_reports import bireports

from .views import excel_reports, filters, dead_inventory, maxweek_data, run_rate, wos, eop, range_metrics_flooring, runratemetrics, combinations, send_linear_regression
from .views import DashboardRankingView, DashboardRunRateView, DashboardHistoryView, DashboardHistoryGraphView
from reports.views.layer2generator import l2_generator
from django.urls import path

from product.views import weeks

app_name = "reports"
urlpatterns = [
    #path('dashboard/rangeMetrics/sales', runratemetrics, name='runrate_metrics'),
    # path("dashboard/rangeMetrics/flooring", range_metrics_flooring,
    #     name="range_metrics_flooring"),
    path("dashboard/inventory/<str:group>",
         InventoryMetricsView.as_view(), name="inventory_metrics"),
    path('dashboard/history/graph',
         DashboardHistoryGraphView.as_view(), name='history_graph'),

    path('runrate/<str:group>',
         run_rate, name='runrate'),
    path('dashboard/history',
         DashboardHistoryView.as_view(), name='history'),
    path('dashboard/<str:group>',
         DashboardDataView.as_view(), name="dashboard_group"),
    path('deadInventoryV2/<str:group>',
         dead_inventoryV2, name='dead_inventory_v2'),
    path('maxWeek',
         maxweek_data, name='maxweek'),
    path('filters/<str:origin>',
         filters, name="filters"),
    path('flooring/<str:group>', flooring, name='flooring'),
    path('flooringPlan/<str:group>', flooring_plan, name='flooring_plan'),

    path("linearRegression", send_linear_regression, name='linearRegression'),


    path('wosV2/<str:group>',
         wosv2, name='wosData_v2'),
    path('weeks', weeks, name="weeks"),
    path('eop', eop),
    path('combinations', combinations),
    path('excel', excel_reports),
    path("layerTwoGenerator", l2_generator),
    path("bireports/<int:id>", bireports)
]
