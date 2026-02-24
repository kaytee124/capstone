from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.mixins import AutoRefreshTokenMixin
from .models import Customer
from .serializers import (
    CustomerRegistrationSerializer,
    AdminCustomerCreationSerializer,
    MissingFieldsError,
    UsernameExistsError,
    EmailExistsError,
    PhoneExistsError,
    InvalidPasswordError,
    InvalidEmailError
)
from accounts.serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class CustomerRegistrationView(APIView):
    """View for customer self-registration"""
    permission_classes = [AllowAny]
    serializer_class = CustomerRegistrationSerializer
    
    def post(self, request):
        """Handle customer registration with custom error codes"""
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create User and Customer
            customer = serializer.save()
            
            # Return success response with user data
            return Response({
                'message': 'Customer registered successfully',
                'user': UserSerializer(customer.user).data,
                'customer_id': customer.id
            }, status=status.HTTP_201_CREATED)
            
        except MissingFieldsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            }
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
            
        except UsernameExistsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'USERNAME_EXISTS',
                'message': 'Username already taken',
                'status_code': 409
            }
            return Response(error_detail, status=status.HTTP_409_CONFLICT)
            
        except EmailExistsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'EMAIL_EXISTS',
                'message': 'Email already registered',
                'status_code': 409
            }
            return Response(error_detail, status=status.HTTP_409_CONFLICT)
            
        except PhoneExistsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'PHONE_EXISTS',
                'message': 'Phone number already registered',
                'status_code': 409
            }
            return Response(error_detail, status=status.HTTP_409_CONFLICT)
            
        except InvalidPasswordError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'INVALID_PASSWORD',
                'message': 'Password must be at least 8 characters',
                'status_code': 422
            }
            return Response(error_detail, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        except InvalidEmailError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'INVALID_EMAIL',
                'message': 'Invalid email format',
                'status_code': 422
            }
            return Response(error_detail, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Customer registration error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Registration failed',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCustomerCreationView(AutoRefreshTokenMixin, APIView):
    """View for admin/employee to create customers with default password"""
    permission_classes = [IsAuthenticated]
    serializer_class = AdminCustomerCreationSerializer
    
    def post(self, request):
        """Handle customer creation by admin/employee"""
        try:
            # Check if user has permission (admin, employee, or superadmin)
            if request.user.role not in ['superadmin', 'admin', 'employee']:
                return Response({
                    'error_code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to create customers',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.serializer_class(
                data=request.data, 
                context={'user': request.user}
            )
            serializer.is_valid(raise_exception=True)
            
            # Create User and Customer with default password
            customer = serializer.save()
            
            # Return success response
            return Response({
                'message': 'Customer created successfully with default password',
                'user': UserSerializer(customer.user).data,
                'customer_id': customer.id,
                'default_password': 'ChangeMe123!',  # Inform admin of default password
                'note': 'Customer must change password on first login'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Admin customer creation error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to create customer',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
