from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import userloginview, userlogoutview, ChangePasswordView

urlpatterns = [
    path('accounts/login/', userloginview.as_view(), name='user_login'),
    path('accounts/logout/', userlogoutview.as_view(), name='user_logout'),
    path('accounts/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('accounts/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('accounts/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
