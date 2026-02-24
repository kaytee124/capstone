from django.urls import path
from rest_framework_simplejwt.views import (
    TokenVerifyView,
)
from .views import (
    userloginview, 
    userlogoutview, 
    ChangePasswordView, 
    TokenRefreshView,
    # Client endpoints
    ClientSelfUpdateView,
    # Admin endpoints
    CreateAdminView,
    AdminSelfUpdateView,
    AdminUpdateEmployeeView,
    # Employee endpoints
    CreateEmployeeView,
    EmployeeSelfUpdateView,
    # Staff endpoints (employee, admin, superadmin)
    StaffUpdateClientView,
    # Superadmin endpoints
    CreateSuperadminView,
    SuperadminUpdateAdminView,
    SuperadminUpdateEmployeeView,
    SuperadminUpdateClientView,
)

urlpatterns = [
    # Authentication endpoints
    path('login/', userloginview.as_view(), name='user_login'),
    path('logout/', userlogoutview.as_view(), name='user_logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Client endpoints
    path('client/update/', ClientSelfUpdateView.as_view(), name='client_self_update'),
    
    # Admin endpoints
    path('admin/create/', CreateAdminView.as_view(), name='create_admin'),
    path('admin/update/', AdminSelfUpdateView.as_view(), name='admin_self_update'),
    path('admin/employee/<int:user_id>/update/', AdminUpdateEmployeeView.as_view(), name='admin_update_employee'),
    
    # Employee endpoints
    path('employee/create/', CreateEmployeeView.as_view(), name='create_employee'),
    path('employee/update/', EmployeeSelfUpdateView.as_view(), name='employee_self_update'),
    
    # Staff endpoints (employee, admin, superadmin can update clients)
    path('staff/client/<int:user_id>/update/', StaffUpdateClientView.as_view(), name='staff_update_client'),
    
    # Superadmin endpoints
    path('superadmin/create/', CreateSuperadminView.as_view(), name='create_superadmin'),
    path('superadmin/admin/<int:user_id>/update/', SuperadminUpdateAdminView.as_view(), name='superadmin_update_admin'),
    path('superadmin/employee/<int:user_id>/update/', SuperadminUpdateEmployeeView.as_view(), name='superadmin_update_employee'),
    path('superadmin/client/<int:user_id>/update/', SuperadminUpdateClientView.as_view(), name='superadmin_update_client'),
]
