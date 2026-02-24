from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import ValidationError
from .models import User
from .mixins import AutoRefreshTokenMixin
from .permissions import IsSuperadmin, IsAdmin, IsAdminOrSuperadmin, IsClient, IsEmployee, IsStaff
from .serializers import (
    UserSerializer, 
    UserListSerializer,
    UserLoginSerializer, 
    ChangePasswordSerializer, 
    UserCreationSerializer,
    ClientSelfUpdateSerializer,
    AdminSelfUpdateSerializer,
    EmployeeSelfUpdateSerializer,
    AdminUpdateEmployeeSerializer,
    StaffUpdateClientSerializer,
    SuperadminUpdateUserSerializer,
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
        """Render login template"""
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        """Handle login API request with custom error codes"""
        try:
            serializer = self.serializer_class(data=request.data)
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
            
            response_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
                'requires_password_change': requires_password_change
            }
            
            # Add warning message if default password is being used
            if requires_password_change:
                response_data['message'] = 'Please change your default password'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
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
                'message': 'Your account has been deactivated',
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
    
    def post(self, request):
        """Handle logout with custom error codes"""
        try:
            # Check if access token is provided in header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header or not auth_header.startswith('Bearer '):
                return Response({
                    'error_code': 'NO_TOKEN',
                    'message': 'Authentication credentials not provided',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if refresh token is provided in body
            refresh_token = request.data.get('refresh')
            if not refresh_token:
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
            
            return Response({
                'message': 'Logged out successfully'
            }, status=status.HTTP_200_OK)
            
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
    
    def put(self, request):
        """Handle change password API request"""
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
            'updated_fields': updated_fields,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

# ============================================================================
# ADMIN ENDPOINTS (Superadmin only)
# ============================================================================

class CreateAdminView(AutoRefreshTokenMixin, APIView):
    """Superadmin creates admin with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsSuperadmin]
    
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
    """Admin can update their own profile - username, email, first_name, last_name only"""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminSelfUpdateSerializer
    
    def patch(self, request):
        """Partial update - only updates fields that are provided"""
        user = request.user
        
        # Ensure admin can only update themselves
        if user.role != 'admin':
            return Response({
                'error_code': 'PERMISSION_DENIED',
                'message': 'Only admins can use this endpoint',
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
            'updated_fields': updated_fields,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

# ============================================================================
# EMPLOYEE ENDPOINTS
# ============================================================================

class CreateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Superadmin or Admin creates employee with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    
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
            'updated_fields': updated_fields,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class AdminUpdateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Admin can update employee status (is_active, is_staff) but NOT role or is_superuser"""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUpdateEmployeeSerializer
    
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
            'updated_fields': updated_fields,
            'user': UserSerializer(employee).data
        }, status=status.HTTP_200_OK)


# ============================================================================
# SUPERADMIN ENDPOINTS (Full control)
# ============================================================================

class CreateSuperadminView(AutoRefreshTokenMixin, APIView):
    """Superadmin creates another superadmin with default password"""
    serializer_class = UserCreationSerializer
    permission_classes = [IsAuthenticated, IsSuperadmin]
    
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
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(admin, field) and getattr(admin, field) != value:
                setattr(admin, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            admin.updated_at = timezone.now()
            admin.updated_by = request.user
            admin.save()
        
        return Response({
            'message': 'Admin updated successfully',
            'updated_fields': updated_fields,
            'user': UserSerializer(admin).data
        }, status=status.HTTP_200_OK)

class SuperadminUpdateEmployeeView(AutoRefreshTokenMixin, APIView):
    """Superadmin can update employee - full control including role promotion"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = SuperadminUpdateUserSerializer
    
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
            'updated_fields': updated_fields,
            'user': UserSerializer(employee).data
        }, status=status.HTTP_200_OK)

class StaffUpdateClientView(AutoRefreshTokenMixin, APIView):
    """Staff (employee, admin, superadmin) can update client status - can change is_active, is_staff, but NOT role"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = StaffUpdateClientSerializer
    
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
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(client, field) and getattr(client, field) != value:
                setattr(client, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            client.updated_at = timezone.now()
            client.updated_by = request.user
            client.save()
        
        return Response({
            'message': 'Client updated successfully',
            'updated_fields': updated_fields,
            'user': UserSerializer(client).data
        }, status=status.HTTP_200_OK)

class SuperadminUpdateClientView(AutoRefreshTokenMixin, APIView):
    """Superadmin can update client - full control including role promotion and deactivation"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = SuperadminUpdateUserSerializer
    
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
        
        # Only update fields that are provided and different
        updated_fields = []
        for field, value in serializer.validated_data.items():
            if hasattr(client, field) and getattr(client, field) != value:
                setattr(client, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            client.updated_at = timezone.now()
            client.updated_by = request.user
            client.save()
        
        return Response({
            'message': 'Client updated successfully',
            'updated_fields': updated_fields,
            'user': UserSerializer(client).data
        }, status=status.HTTP_200_OK)


class getalladminsview(AutoRefreshTokenMixin, APIView):
    """Superadmin can get all admins - returns only first_name, last_name, email, and status"""
    permission_classes = [IsAuthenticated, IsSuperadmin]
    serializer_class = UserListSerializer
    
    def get(self, request):
        """Get all admins"""
        admins = User.objects.filter(role='admin')
        return Response(UserListSerializer(admins, many=True).data, status=status.HTTP_200_OK)

class getallemployeesview(AutoRefreshTokenMixin, APIView):
    """Admin or Superadmin can get all employees - returns only first_name, last_name, email, and status"""
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = UserListSerializer
    
    def get(self, request):
        """Get all employees"""
        employees = User.objects.filter(role='employee')
        return Response(UserListSerializer(employees, many=True).data, status=status.HTTP_200_OK)

class getallclientsview(AutoRefreshTokenMixin, APIView):
    """Staff can get all clients - returns only first_name, last_name, email, and status"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = UserListSerializer
    
    def get(self, request):
        """Get all clients"""
        clients = User.objects.filter(role='client')
        return Response(UserListSerializer(clients, many=True).data, status=status.HTTP_200_OK)