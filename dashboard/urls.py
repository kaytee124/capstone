from django.urls import path
from .views import DashboardMetricsView, RevenueReportView

urlpatterns = [
    path('', DashboardMetricsView.as_view(), name='dashboard_home'),
    path('metrics/', DashboardMetricsView.as_view(), name='dashboard_metrics'),
    path('revenue-report/', RevenueReportView.as_view(), name='revenue_report'),
]
