from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotAuthenticated
from .models import User
from .mixins import AutoRefreshTokenMixin
from .permissions import IsSuperadmin, IsAdmin, IsAdminOrSuperadmin, IsClient, IsEmployee, IsStaff
from .serializers import (
    UserSerializer, 
    UserListSerializer,
    ClientListSerializer,
    UserByIdSerializer,
    UserLoginSerializer, 
    ChangePasswordSerializer, 
    UserCreationSerializer,
    ClientSelfUpdateSerializer,
    AdminSelfUpdateSerializer,
    AccountInactiveError,
    InvalidCredentialsError,
    MissingFieldsError,
    EmployeeSelfUpdateSerializer,
    AdminUpdateEmployeeSerializer,
    StaffUpdateClientSerializer,
    SuperadminUpdateUserSerializer,
    UserUpdateSerializer,
    staffGetUserByIdSerializer,
    InvalidCredentialsError,
    AccountInactiveError,
    MissingFieldsError
)
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class userloginview(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def get(self, request):
        """Render login template with error messages and redirect URL"""
        error = request.GET.get('error')
        message = request.GET.get('message', '')
        next_url = request.GET.get('next', '')
        
        context = {
            'error': error,
            'error_message': message,
            'next_url': next_url
        }
        return render(request, 'accounts/login.html', context)
    
    def post(self, request):
        """Handle login API request with custom error codes"""
        try:
            serializer = self.serializer_class(data=request.data)
            
            # Validate without raising exception first to check for AccountInactiveError
            if not serializer.is_valid():
                errors = serializer.errors
                error_msg = None
                
                # Check for AccountInactiveError in non_field_errors
                if 'non_field_errors' in errors:
                    error_list = errors['non_field_errors']
                    if isinstance(error_list, list) and len(error_list) > 0:
                        error_msg = str(error_list[0])
                
                # Also check if the error detail itself contains the message
                if not error_msg:
                    for key, value in errors.items():
                        if isinstance(value, list) and len(value) > 0:
                            error_str = str(value[0])
                            if 'deactivated' in error_str.lower() or 'inactive' in error_str.lower():
                                error_msg = error_str
                                break
                        elif isinstance(value, dict):
                            msg = value.get('message', '')
                            if 'deactivated' in str(msg).lower() or 'inactive' in str(msg).lower():
                                error_msg = str(msg)
                                break
                
                # Check if it's an AccountInactiveError message
                if error_msg and ('deactivated' in error_msg.lower() or 'inactive' in error_msg.lower()):
                    return Response({
                        'error_code': 'ACCOUNT_INACTIVE',
                        'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                        'status_code': 401
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # For other validation errors, raise exception normally
                serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']
            
            # Check if user is using default password
            from django.conf import settings
            requires_password_change = user.check_password(settings.DEFAULT_CUSTOMER_PASSWORD)
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response_data = {
                'refresh': refresh_token,
                'access': access_token,
                'user': UserSerializer(user).data,
                'requires_password_change': requires_password_change
            }
            
            # Add warning message if default password is being used
            if requires_password_change:
                response_data['message'] = 'Please change your default password'
            
            # Create response and set cookies for browser navigation
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # Set HTTP-only cookies for token storage (as backup for browser navigation)
            # Note: JavaScript will still use localStorage for API calls
            response.set_cookie(
                'access_token',
                access_token,
                max_age=3600,  # 1 hour (matches ACCESS_TOKEN_LIFETIME)
                httponly=False,  # Allow JavaScript access
                samesite='Lax',
                secure=False
            )
            response.set_cookie(
                'refresh_token',
                refresh_token,
                max_age=86400,  # 1 day (matches REFRESH_TOKEN_LIFETIME)
                httponly=False,  # Allow JavaScript access
                samesite='Lax',
                secure=False
            )
            
            return response
            
        except MissingFieldsError as e:
            # Handle missing fields error
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'MISSING_FIELDS',
                'message': 'Username and password are required',
                'status_code': 400
            }
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
            
        except InvalidCredentialsError as e:
            # Handle invalid credentials error
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'INVALID_CREDENTIALS',
                'message': 'Invalid username or password',
                'status_code': 401
            }
            return Response(error_detail, status=status.HTTP_401_UNAUTHORIZED)
            
        except AccountInactiveError as e:
            # Handle inactive account error
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'ACCOUNT_INACTIVE',
                'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                'status_code': 401
            }
            return Response(error_detail, status=status.HTTP_401_UNAUTHORIZED)
            
        except ValidationError as e:
            # Handle other validation errors (fallback)
            error_detail = e.detail if hasattr(e, 'detail') else str(e)
            return Response({
                'error_code': 'VALIDATION_ERROR',
                'message': error_detail,
                'status_code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Login error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class userlogoutview(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Handle logout via GET (for sidebar link)"""
        return self._handle_logout(request)
    
    def post(self, request):
        """Handle logout via POST (for API calls)"""
        return self._handle_logout(request)
    
    def _handle_logout(self, request):
        """Handle logout with custom error codes"""
        try:
            # Check if this is a GET request (browser navigation)
            is_get_request = request.method == 'GET'
            
            # Check if access token is provided in header or cookie
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            access_token = None
            
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
            elif not auth_header:
                # Try to get from cookie
                access_token = request.COOKIES.get('access_token')
                if access_token:
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            
            if not access_token:
                # For GET requests, redirect to login
                if is_get_request:
                    return redirect(reverse('user_login') + '?message=Please log in again')
                return Response({
                    'error_code': 'NO_TOKEN',
                    'message': 'Authentication credentials not provided',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get refresh token from body, query params, or cookies
            refresh_token = (
                request.data.get('refresh') or  # POST body
                request.GET.get('refresh') or  # GET query param
                request.COOKIES.get('refresh_token')  # Cookie
            )
            
            if not refresh_token:
                # For GET requests without refresh token, just clear cookies and redirect
                if is_get_request:
                    response = redirect(reverse('user_login'))
                    response.delete_cookie('access_token')
                    response.delete_cookie('refresh_token')
                    return response
                return Response({
                    'error_code': 'MISSING_TOKEN',
                    'message': 'Refresh token is required',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to blacklist the refresh token
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError as e:
                # Handle invalid or expired refresh token
                return Response({
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                # Handle other token-related errors
                logger.warning(f'Token blacklist error: {str(e)}')
                return Response({
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Create response and clear cookies
            if is_get_request:
                # For GET requests, redirect to login page
                response = redirect(reverse('user_login') + '?message=Logged out successfully')
            else:
                # For POST requests, return JSON response
                response = Response({
                    'message': 'Logged out successfully'
                }, status=status.HTTP_200_OK)
            
            # Clear token cookies
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Logout error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Logout failed',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TokenRefreshView(APIView):
    """Custom token refresh view with custom error codes - works like default Simple JWT view"""
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer
    
    def post(self, request):
        """Handle token refresh with custom error codes"""
        try:
            # Check if refresh token is provided
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'error_code': 'MISSING_TOKEN',
                    'message': 'Refresh token is required',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use Simple JWT's serializer to handle rotation and blacklisting
            serializer = self.serializer_class(data=request.data)
            
            try:
                serializer.is_valid(raise_exception=True)
                # Serializer handles token rotation and blacklisting automatically
                return Response(serializer.validated_data, status=status.HTTP_200_OK)
                
            except TokenError as e:
                # Handle invalid or expired token
                return Response({
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired refresh token',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            except ValidationError as e:
                # Handle validation errors (usually means invalid token)
                return Response({
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired refresh token',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Token refresh error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Token refresh failed',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    """
    Change password endpoint.
    Requires JWT token authentication - user can only change their own password.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def get(self, request):
        """Render change password template"""
        return render(request, 'accounts/change_password.html')
    
    def post(self, request):
        """Handle change password API request (POST for form submission)"""
        # request.user is automatically set from the JWT token
        # This ensures the user can only change their own password
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Clear the requires_password_change flag
        response_data = {
            'message': 'Password changed successfully',
            'password_changed': True
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Handle change password API request (PUT for API calls)"""
        # request.user is automatically set from the JWT token
        # This ensures the user can only change their own password
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


# ============================================================================
# CLIENT ENDPOINTS
# ============================================================================

class ClientSelfUpdateView(AutoRefreshTokenMixin, APIView):
    """Client can update their own profile - username, email, first_name, last_name only"""
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = ClientSelfUpdateSerializer
    
    def get(self, request):
        """Render update profile template"""
        return render(request, 'accounts/client_update.html')
    
    def patch(self, request):
        """Partial update - only updates fields that are provided"""
        user = request.user
        
        # Ensure client can only update themselves
        if user.role != 'client':
            return Response({
                'error_code': 'PERMISSION_DENIED',
                'message': 'Only clients can use this endpoint',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.serializer_class(
            user, 
            data=request.data, 
            partial=True,
            context={'user': user}
        )
        serializer.is_valid(raise_exception=True)
        
        # Use serializer's update method which handles both User and Customer fields
        serializer.save()
        
        # Refresh user from database to get updated customer data
        user.refresh_from_db()
        if hasattr(user, 'customer_profile'):
            user.customer_profile.refresh_from_db()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

# ============================================================================
# ADMIN ENDPOINTS (Superadmin only)
# ============================================================================

class CreateAdminView(AutoRefreshTokenMixin, APIView):
    """Superadmin creates admin with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsSuperadmin]
    
    def get(self, request):
        """Render create admin template"""
        return render(request, 'accounts/create_admin.html')
    
    def post(self, request):
        from django.conf import settings
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user with default password
        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=settings.DEFAULT_CUSTOMER_PASSWORD,
            username=serializer.validated_data['username'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            role='admin',
            is_active=True,
            is_staff=True,
            is_superuser=False
        )
        
        user.updated_by = request.user
        user.save()
        
        return Response({
            'message': 'Admin created successfully with default password',
            'user': UserSerializer(user).data,
            'default_password': settings.DEFAULT_CUSTOMER_PASSWORD,
            'note': 'Admin must change password on first login'
        }, status=status.HTTP_201_CREATED)

class AdminSelfUpdateView(AutoRefreshTokenMixin, APIView):
    """Admin and Superadmin can update their own profile - username, email, first_name, last_name only"""
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = AdminSelfUpdateSerializer
    
    def get(self, request):
        """Render admin update profile template"""
        return render(request, 'accounts/admin_update.html')
    
    def patch(self, request):
        """Partial update - only updates fields that are provided"""
        user = request.user
        
        # Ensure admin or superadmin can only update themselves
        if user.role not in ['admin', 'superadmin']:
            return Response({
                'error_code': 'PERMISSION_DENIED',
                'message': 'Only admins and superadmins can use this endpoint',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.serializer_class(
            user, 
            data=request.data, 
            partial=True,
            context={'user': user}
        )
        serializer.is_valid(raise_exception=True)
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(user, field) and getattr(user, field) != value:
                setattr(user, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            user.updated_at = timezone.now()
            user.updated_by = user
            user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

# ============================================================================
# EMPLOYEE ENDPOINTS
# ============================================================================

class CreateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Superadmin or Admin creates employee with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    
    def get(self, request):
        """Render create employee template"""
        return render(request, 'accounts/create_employee.html')
    
    def post(self, request):
        from django.conf import settings
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user with default password
        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=settings.DEFAULT_CUSTOMER_PASSWORD,
            username=serializer.validated_data['username'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            role='employee',
            is_active=True,
            is_staff=True,
            is_superuser=False
        )
        
        user.updated_by = request.user
        user.save()
        
        return Response({
            'message': 'Employee created successfully with default password',
            'user': UserSerializer(user).data,
            'default_password': settings.DEFAULT_CUSTOMER_PASSWORD,
            'note': 'Employee must change password on first login'
        }, status=status.HTTP_201_CREATED)

class EmployeeSelfUpdateView(AutoRefreshTokenMixin, APIView):
    """Employee can update their own profile - username, email, first_name, last_name only"""
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = EmployeeSelfUpdateSerializer
    
    def get(self, request):
        """Render employee update profile template"""
        return render(request, 'accounts/employee_update.html')
    
    def patch(self, request):
        """Partial update - only updates fields that are provided"""
        user = request.user
        
        # Ensure employee can only update themselves
        if user.role != 'employee':
            return Response({
                'error_code': 'PERMISSION_DENIED',
                'message': 'Only employees can use this endpoint',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.serializer_class(
            user, 
            data=request.data, 
            partial=True,
            context={'user': user}
        )
        serializer.is_valid(raise_exception=True)
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(user, field) and getattr(user, field) != value:
                setattr(user, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            user.updated_at = timezone.now()
            user.updated_by = user
            user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class AdminUpdateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Admin can update employee status (is_active, is_staff) but NOT role or is_superuser"""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUpdateEmployeeSerializer
    
    def get(self, request, user_id):
        """Render update employee template"""
        return render(request, 'accounts/admin_update_employee.html', {'user_id': user_id})
    
    def patch(self, request, user_id):
        """Partial update employee - admin can change status but not role"""
        try:
            employee = User.objects.get(id=user_id, role='employee')
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'Employee not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(
            employee, 
            data=request.data, 
            partial=True,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(employee, field) and getattr(employee, field) != value:
                setattr(employee, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            employee.updated_at = timezone.now()
            employee.updated_by = request.user
            employee.save()
        
        return Response({
            'message': 'Employee updated successfully',
            'user': UserSerializer(employee).data
        }, status=status.HTTP_200_OK)


# ============================================================================
# SUPERADMIN ENDPOINTS (Full control)
# ============================================================================

class CreateSuperadminView(AutoRefreshTokenMixin, APIView):
    """Superadmin creates another superadmin with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsSuperadmin]
    
    def get(self, request):
        """Render create superadmin template"""
        return render(request, 'accounts/create_superadmin.html')
    
    def post(self, request):
        from django.conf import settings
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user with default password
        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=settings.DEFAULT_CUSTOMER_PASSWORD,
            username=serializer.validated_data['username'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            role='superadmin',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        
        user.updated_by = request.user
        user.save()
        
        return Response({
            'message': 'Superadmin created successfully with default password',
            'user': UserSerializer(user).data,
            'default_password': settings.DEFAULT_CUSTOMER_PASSWORD,
            'note': 'Superadmin must change password on first login'
        }, status=status.HTTP_201_CREATED)

class SuperadminUpdateAdminView(AutoRefreshTokenMixin, APIView):
    """Superadmin can update admin - full control including role promotion"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = SuperadminUpdateUserSerializer
    
    def get(self, request, user_id):
        """Render update admin template"""
        return render(request, 'accounts/superadmin_update_admin.html', {'user_id': user_id})
    
    def patch(self, request, user_id):
        """Partial update admin - only updates fields that are provided"""
        try:
            admin = User.objects.get(id=user_id, role='admin')
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'Admin not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(
            admin, 
            data=request.data, 
            partial=True,
            context={'user': request.user, 'target_user': admin}
        )
        serializer.is_valid(raise_exception=True)
        
        # Use serializer's update method which handles role-based is_staff/is_superuser updates
        serializer.save()
        
        # Refresh admin from database to get updated data
        admin.refresh_from_db()
        
        return Response({
            'message': 'Admin updated successfully',
            'user': UserSerializer(admin).data
        }, status=status.HTTP_200_OK)

class SuperadminUpdateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Superadmin can update employee - full control including role promotion"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = SuperadminUpdateUserSerializer
    
    def get(self, request, user_id):
        """Render update employee template"""
        return render(request, 'accounts/superadmin_update_employee.html', {'user_id': user_id})
    
    def patch(self, request, user_id):
        """Partial update employee - only updates fields that are provided"""
        try:
            employee = User.objects.get(id=user_id, role='employee')
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'Employee not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(
            employee, 
            data=request.data, 
            partial=True,
            context={'user': request.user, 'target_user': employee}
        )
        serializer.is_valid(raise_exception=True)
        
        # Use serializer's update method which handles role-based is_staff/is_superuser updates
        serializer.save()
        
        # Refresh employee from database to get updated data
        employee.refresh_from_db()
        
        return Response({
            'message': 'Employee updated successfully',
            'user': UserSerializer(employee).data
        }, status=status.HTTP_200_OK)

class StaffUpdateClientView(AutoRefreshTokenMixin, APIView):
    """Staff (employee, admin, superadmin) can update client status - can change is_active, is_staff, but NOT role"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = StaffUpdateClientSerializer
    
    def get(self, request, user_id):
        """Render update client template"""
        return render(request, 'accounts/staff_update_client.html', {'user_id': user_id})
    
    def patch(self, request, user_id):
        """Partial update client - only updates fields that are provided (no role changes)"""
        try:
            client = User.objects.get(id=user_id, role='client')
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'Client not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(
            client, 
            data=request.data, 
            partial=True,
            context={'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        
        # Use serializer's update method which handles both User and Customer fields
        serializer.save()
        
        # Refresh client from database to get updated customer data
        client.refresh_from_db()
        if hasattr(client, 'customer_profile'):
            client.customer_profile.refresh_from_db()
        
        return Response({
            'message': 'Client updated successfully',
            'user': staffGetUserByIdSerializer(client).data
        }, status=status.HTTP_200_OK)

class SuperadminUpdateClientView(AutoRefreshTokenMixin, APIView):
    """Superadmin can update client - full control including role promotion and deactivation"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = SuperadminUpdateUserSerializer
    
    def get(self, request, user_id):
        """Render update client template"""
        return render(request, 'accounts/superadmin_update_client.html', {'user_id': user_id})
    
    def patch(self, request, user_id):
        """Partial update client - only updates fields that are provided"""
        try:
            client = User.objects.get(id=user_id, role='client')
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'Client not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(
            client, 
            data=request.data, 
            partial=True,
            context={'user': request.user, 'target_user': client}
        )
        serializer.is_valid(raise_exception=True)
        
        # Use serializer's update method which handles both User and Customer fields
        serializer.save()
        
        # Refresh client from database to get updated customer data
        client.refresh_from_db()
        if hasattr(client, 'customer_profile'):
            client.customer_profile.refresh_from_db()
        
        return Response({
            'message': 'Client updated successfully',
            'user': UserUpdateSerializer(client).data
        }, status=status.HTTP_200_OK)


class getalladminsview(AutoRefreshTokenMixin, APIView):
    """Superadmin can get all admins - returns only first_name, last_name, email, and status"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = UserListSerializer
    
    def get(self, request):
        """Get all admins with pagination, filtering, and search - render template or return JSON"""
        # Check if this is an API request
        if request.headers.get('Accept', '').startswith('application/json'):
            return self._get_admins_json(request)
        else:
            # Render HTML template
            return render(request, 'accounts/admins_list.html')
    
    def _get_admins_json(self, request):
        """Get all admins with pagination, filtering, and search"""
        try:
            # Base queryset - filter by admin role
            queryset = User.objects.filter(role='admin')
            
            # Apply filters
            role_filter = request.query_params.get('role')
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            is_active_filter = request.query_params.get('is_active')
            if is_active_filter is not None:
                is_active_bool = is_active_filter.lower() in ('true', '1', 'yes')
                queryset = queryset.filter(is_active=is_active_bool)
            
            # Apply search
            search_term = request.query_params.get('search')
            if search_term:
                queryset = queryset.filter(
                    Q(username__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term)
                )
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Validate page_size (max 100)
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 20
            if page < 1:
                page = 1
            
            # Calculate pagination
            total_count = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated results
            admins = queryset.order_by('id')[start:end]
            
            # Serialize data
            serializer = UserListSerializer(admins, many=True)
            
            return Response({
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except (AuthenticationFailed, NotAuthenticated, InvalidToken) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN' if isinstance(e, NotAuthenticated) else 'INVALID_TOKEN',
                'message': 'Authentication credentials not provided' if isinstance(e, NotAuthenticated) else 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f'Failed to retrieve admins: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve users',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class getallemployeesview(AutoRefreshTokenMixin, APIView):
    """Admin or Superadmin can get all employees - returns only first_name, last_name, email, and status"""
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = UserListSerializer
    
    def get(self, request):
        """Get all employees with pagination, filtering, and search - render template or return JSON"""
        # Check if this is an API request
        if request.headers.get('Accept', '').startswith('application/json'):
            return self._get_employees_json(request)
        else:
            # Render HTML template
            return render(request, 'accounts/employees_list.html')
    
    def _get_employees_json(self, request):
        """Get all employees with pagination, filtering, and search"""
        try:
            # Base queryset - filter by employee role
            queryset = User.objects.filter(role='employee')
            
            # Apply filters
            role_filter = request.query_params.get('role')
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            is_active_filter = request.query_params.get('is_active')
            if is_active_filter is not None:
                is_active_bool = is_active_filter.lower() in ('true', '1', 'yes')
                queryset = queryset.filter(is_active=is_active_bool)
            
            # Apply search
            search_term = request.query_params.get('search')
            if search_term:
                queryset = queryset.filter(
                    Q(username__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term)
                )
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Validate page_size (max 100)
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 20
            if page < 1:
                page = 1
            
            # Calculate pagination
            total_count = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated results
            employees = queryset.order_by('id')[start:end]
            
            # Serialize data
            serializer = UserListSerializer(employees, many=True)
            
            return Response({
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except (AuthenticationFailed, NotAuthenticated, InvalidToken) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN' if isinstance(e, NotAuthenticated) else 'INVALID_TOKEN',
                'message': 'Authentication credentials not provided' if isinstance(e, NotAuthenticated) else 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f'Failed to retrieve employees: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve users',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class getallclientsview(AutoRefreshTokenMixin, APIView):
    """Staff can get all clients - returns first_name, last_name, email, status, and customer fields"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = ClientListSerializer
    
    def get(self, request):
        """Get all clients with pagination, filtering, and search - render template or return JSON"""
        # Check if this is an API request
        if request.headers.get('Accept', '').startswith('application/json'):
            return self._get_clients_json(request)
        else:
            # Render HTML template
            return render(request, 'accounts/clients_list.html')
    
    def _get_clients_json(self, request):
        """Get all clients with pagination, filtering, and search"""
        try:
            # Base queryset - filter by client role, use select_related to optimize customer_profile queries
            queryset = User.objects.filter(role='client').select_related('customer_profile')
            
            # Apply filters
            role_filter = request.query_params.get('role')
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            is_active_filter = request.query_params.get('is_active')
            if is_active_filter is not None:
                is_active_bool = is_active_filter.lower() in ('true', '1', 'yes')
                queryset = queryset.filter(is_active=is_active_bool)
            
            # Apply search
            search_term = request.query_params.get('search')
            if search_term:
                queryset = queryset.filter(
                    Q(username__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term)
                )
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Validate page_size (max 100)
            if page_size > 100:
                page_size = 100
            if page_size < 1:
                page_size = 20
            if page < 1:
                page = 1
            
            # Calculate pagination
            total_count = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated results
            clients = queryset.order_by('id')[start:end]
            
            # Serialize data
            serializer = ClientListSerializer(clients, many=True)
            
            return Response({
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except (AuthenticationFailed, NotAuthenticated, InvalidToken) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN' if isinstance(e, NotAuthenticated) else 'INVALID_TOKEN',
                'message': 'Authentication credentials not provided' if isinstance(e, NotAuthenticated) else 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f'Failed to retrieve clients: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve users',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserByIdView(AutoRefreshTokenMixin, APIView):
    """User can get their own profile - returns first_name, last_name, email, status, and customer fields if user is a client"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserByIdSerializer

    def get(self, request):
        """Get current user's profile - render template for GET, return JSON for API calls"""
        try:
            # Check if this is an API request (Accept: application/json header)
            if request.headers.get('Accept', '').startswith('application/json'):
                # Optimize query for clients to include customer profile
                user = request.user
                if user.role == 'client':
                    # Use select_related to avoid N+1 query
                    from .models import User
                    user = User.objects.select_related('customer_profile').get(id=user.id)
                
                return Response({
                    'message': 'User profile retrieved successfully',
                    'user': UserByIdSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                # Render HTML template
                return render(request, 'accounts/profile.html', {
                    'user': request.user
                })
        except Exception as e:
            logger.error(f'Failed to retrieve user profile: {str(e)}', exc_info=True)
            if request.headers.get('Accept', '').startswith('application/json'):
                return Response({
                    'error_code': 'SERVER_ERROR',
                    'message': 'Failed to retrieve user profile',
                    'status_code': 500
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return render(request, 'accounts/profile.html', {
                    'error': 'Failed to load profile'
                })

class staffGetUserByIdView(AutoRefreshTokenMixin, APIView):
    """Staff (employee, admin, superadmin) can get user by id"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = staffGetUserByIdSerializer

    def get(self, request, user_id):
        """Get user by id - render template for HTML, return JSON for API"""
        # Check if this is an API request
        if request.headers.get('Accept', '').startswith('application/json'):
            return self._get_user_json(request, user_id)
        else:
            # Render HTML template
            return render(request, 'accounts/staff_user_by_id.html', {'user_id': user_id})
    
    def _get_user_json(self, request, user_id):
        """Get user by id - return JSON"""
        try:
            # Use select_related to optimize query for customer profile
            user = User.objects.select_related('customer_profile').get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'User not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Failed to retrieve user: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve user',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'User profile retrieved successfully',
            'user': staffGetUserByIdSerializer(user).data
        }, status=status.HTTP_200_OK)

class superadminGetUserByIdView(AutoRefreshTokenMixin, APIView):
    """Superadmin can get user by id - returns full user details"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = UserUpdateSerializer

    def get(self, request, user_id):
        """Get user by id - render template for HTML, return JSON for API"""
        # Check if this is an API request
        if request.headers.get('Accept', '').startswith('application/json'):
            return self._get_user_json(request, user_id)
        else:
            # Render HTML template
            return render(request, 'accounts/superadmin_user_by_id.html', {'user_id': user_id})
    
    def _get_user_json(self, request, user_id):
        """Get user by id - return JSON"""
        try:
            # Use select_related to optimize query for customer profile
            user = User.objects.select_related('customer_profile').get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error_code': 'NOT_FOUND',
                'message': 'User not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Failed to retrieve user: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve user',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'User profile retrieved successfully',
            'user': UserUpdateSerializer(user).data
        }, status=status.HTTP_200_OK)