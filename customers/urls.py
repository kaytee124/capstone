from django.urls import path
from .views import CustomerRegistrationView, AdminCustomerCreationView

urlpatterns = [
    path('register/', CustomerRegistrationView.as_view(), name='customer_register'),
    path('create/', AdminCustomerCreationView.as_view(), name='admin_create_customer'),
]
