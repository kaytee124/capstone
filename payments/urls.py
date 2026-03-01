from django.urls import path
from .views import PaymentInitializeView, PaymentCallbackView

urlpatterns = [
    path('initialize/', PaymentInitializeView.as_view(), name='payment_initialize'),
    path('callback/', PaymentCallbackView.as_view(), name='payment_callback'),
]

