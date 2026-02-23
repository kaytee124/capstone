from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import userloginview, userlogoutview, ChangePasswordView

urlpatterns = [
    path('login/', userloginview.as_view(), name='user_login'),
    path('logout/', userlogoutview.as_view(), name='user_logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
