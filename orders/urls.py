from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.OrderListView.as_view(), name='orders_list'),
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('<int:id>/update/', views.OrderUpdateView.as_view(), name='order_update'),
    path('<int:id>/', views.OrderDetailView.as_view(), name='order_detail'),
]
