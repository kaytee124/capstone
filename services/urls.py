from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.ServiceListView.as_view(), name='services_list'),
    path('create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('<int:id>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('<int:id>/update/', views.ServiceUpdateView.as_view(), name='service_update'),
]