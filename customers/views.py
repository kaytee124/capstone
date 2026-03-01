from django.shortcuts import render
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotAuthenticated
from rest_framework_simplejwt.exceptions import InvalidToken
from accounts.mixins import AutoRefreshTokenMixin
from .models import Customer
from accounts.permissions import IsStaff
from .serializers import (
    CustomerRegistrationSerializer,
    AdminCustomerCreationSerializer,
    MissingFieldsError,
    UsernameExistsError,
    EmailExistsError,
    PhoneExistsError,
    WhatsAppExistsError,
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
    
    def get(self, request):
        """Render registration template"""
        return render(request, 'customers/register.html')
    
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
            
        except (AuthenticationFailed, NotAuthenticated, InvalidToken) as e:
            # Handle authentication errors (for consistency, even though AllowAny is set)
            return Response({
                'error_code': 'NO_TOKEN' if isinstance(e, NotAuthenticated) else 'INVALID_TOKEN',
                'message': 'Authentication credentials not provided' if isinstance(e, NotAuthenticated) else 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
        
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
        
        except WhatsAppExistsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'WHATSAPP_EXISTS',
                'message': 'WhatsApp number already registered',
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
        
        except ValidationError as e:
            # Extract specific error message from ValidationError
            error_message = 'Invalid data provided'
            error_code = 'VALIDATION_ERROR'
            
            # Helper function to extract string from ErrorDetail or regular value
            def extract_string(value):
                if hasattr(value, 'string'):
                    return str(value.string)
                elif hasattr(value, '__str__'):
                    return str(value)
                else:
                    return str(value)
            
            # Check if it's a custom exception with detail
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    # Check for nested error structures (field-level errors)
                    for field, errors in e.detail.items():
                        if isinstance(errors, dict):
                            # Check if it's our custom error format with ErrorDetail objects
                            if 'message' in errors:
                                error_message = extract_string(errors['message'])
                                if 'error_code' in errors:
                                    error_code = extract_string(errors['error_code'])
                                break
                            # Also check if error_code exists without message (map to message)
                            elif 'error_code' in errors:
                                code = extract_string(errors['error_code'])
                                if code == 'PHONE_EXISTS':
                                    error_message = 'Phone number already registered'
                                elif code == 'WHATSAPP_EXISTS':
                                    error_message = 'WhatsApp number already registered'
                                elif code == 'EMAIL_EXISTS':
                                    error_message = 'Email already registered'
                                elif code == 'USERNAME_EXISTS':
                                    error_message = 'Username already taken'
                                error_code = code
                                break
                        elif isinstance(errors, list) and len(errors) > 0:
                            # Check first error in list
                            first_error = errors[0]
                            if isinstance(first_error, dict):
                                if 'message' in first_error:
                                    error_message = extract_string(first_error['message'])
                                    if 'error_code' in first_error:
                                        error_code = extract_string(first_error['error_code'])
                                elif 'error_code' in first_error:
                                    # Map error code to message
                                    code = extract_string(first_error['error_code'])
                                    if code == 'PHONE_EXISTS':
                                        error_message = 'Phone number already registered'
                                    elif code == 'WHATSAPP_EXISTS':
                                        error_message = 'WhatsApp number already registered'
                                    elif code == 'EMAIL_EXISTS':
                                        error_message = 'Email already registered'
                                    elif code == 'USERNAME_EXISTS':
                                        error_message = 'Username already taken'
                                    error_code = code
                            else:
                                error_message = extract_string(first_error)
                            break
                    # If no field errors found, check top-level message
                    if error_message == 'Invalid data provided' and 'message' in e.detail:
                        error_message = extract_string(e.detail['message'])
                        if 'error_code' in e.detail:
                            error_code = extract_string(e.detail['error_code'])
                elif isinstance(e.detail, (list, str)):
                    error_message = extract_string(e.detail) if isinstance(e.detail, str) else extract_string(e.detail[0]) if e.detail else error_message
            
            return Response({
                'error_code': error_code,
                'message': error_message,
                'status_code': 422
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        except IntegrityError as e:
            # Handle database integrity errors (duplicate keys, etc.)
            error_message = str(e)
            if 'whatsapp_number' in error_message.lower() or 'whatsapp_number_key' in error_message.lower():
                return Response({
                    'error_code': 'WHATSAPP_EXISTS',
                    'message': 'WhatsApp number already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'phone_number' in error_message.lower() or 'phone_number_key' in error_message.lower():
                return Response({
                    'error_code': 'PHONE_EXISTS',
                    'message': 'Phone number already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'username' in error_message.lower():
                return Response({
                    'error_code': 'USERNAME_EXISTS',
                    'message': 'Username already taken',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'email' in error_message.lower():
                return Response({
                    'error_code': 'EMAIL_EXISTS',
                    'message': 'Email already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            else:
                logger.error(f'Database integrity error: {str(e)}', exc_info=True)
                return Response({
                    'error_code': 'DUPLICATE_ENTRY',
                    'message': 'A record with this information already exists',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Customer registration error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to create customer',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCustomerCreationView(AutoRefreshTokenMixin, APIView):
    """View for superadmin/admin/employee to create customers with default password"""
    permission_classes = [IsAuthenticated, IsStaff]
    serializer_class = AdminCustomerCreationSerializer
    
    def get(self, request):
        """Render create customer template"""
        return render(request, 'customers/create_customer.html')
    
    def post(self, request):
        """Handle customer creation by superadmin/admin/employee with custom error codes"""
        try:
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
            
        except (AuthenticationFailed, NotAuthenticated, InvalidToken) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN' if isinstance(e, NotAuthenticated) else 'INVALID_TOKEN',
                'message': 'Authentication credentials not provided' if isinstance(e, NotAuthenticated) else 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        except MissingFieldsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            }
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        except WhatsAppExistsError as e:
            error_detail = e.detail if hasattr(e, 'detail') else {
                'error_code': 'WHATSAPP_EXISTS',
                'message': 'WhatsApp number already registered',
                'status_code': 409
            }
            return Response(error_detail, status=status.HTTP_409_CONFLICT)
        
        except ValidationError as e:
            # Extract specific error message from ValidationError
            error_message = 'Invalid data provided'
            error_code = 'VALIDATION_ERROR'
            
            # Helper function to extract string from ErrorDetail or regular value
            def extract_string(value):
                if hasattr(value, 'string'):
                    return str(value.string)
                elif hasattr(value, '__str__'):
                    return str(value)
                else:
                    return str(value)
            
            # Check if it's a custom exception with detail
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    # Check for nested error structures (field-level errors)
                    for field, errors in e.detail.items():
                        if isinstance(errors, dict):
                            # Check if it's our custom error format with ErrorDetail objects
                            if 'message' in errors:
                                error_message = extract_string(errors['message'])
                                if 'error_code' in errors:
                                    error_code = extract_string(errors['error_code'])
                                break
                            # Also check if error_code exists without message (map to message)
                            elif 'error_code' in errors:
                                code = extract_string(errors['error_code'])
                                if code == 'PHONE_EXISTS':
                                    error_message = 'Phone number already registered'
                                elif code == 'WHATSAPP_EXISTS':
                                    error_message = 'WhatsApp number already registered'
                                elif code == 'EMAIL_EXISTS':
                                    error_message = 'Email already registered'
                                elif code == 'USERNAME_EXISTS':
                                    error_message = 'Username already taken'
                                error_code = code
                                break
                        elif isinstance(errors, list) and len(errors) > 0:
                            # Check first error in list
                            first_error = errors[0]
                            if isinstance(first_error, dict):
                                if 'message' in first_error:
                                    error_message = extract_string(first_error['message'])
                                    if 'error_code' in first_error:
                                        error_code = extract_string(first_error['error_code'])
                                elif 'error_code' in first_error:
                                    # Map error code to message
                                    code = extract_string(first_error['error_code'])
                                    if code == 'PHONE_EXISTS':
                                        error_message = 'Phone number already registered'
                                    elif code == 'WHATSAPP_EXISTS':
                                        error_message = 'WhatsApp number already registered'
                                    elif code == 'EMAIL_EXISTS':
                                        error_message = 'Email already registered'
                                    elif code == 'USERNAME_EXISTS':
                                        error_message = 'Username already taken'
                                    error_code = code
                            else:
                                error_message = extract_string(first_error)
                            break
                    # If no field errors found, check top-level message
                    if error_message == 'Invalid data provided' and 'message' in e.detail:
                        error_message = extract_string(e.detail['message'])
                        if 'error_code' in e.detail:
                            error_code = extract_string(e.detail['error_code'])
                elif isinstance(e.detail, (list, str)):
                    error_message = extract_string(e.detail) if isinstance(e.detail, str) else extract_string(e.detail[0]) if e.detail else error_message
            
            return Response({
                'error_code': error_code,
                'message': error_message,
                'status_code': 422
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        except IntegrityError as e:
            # Handle database integrity errors (duplicate keys, etc.)
            error_message = str(e)
            if 'whatsapp_number' in error_message.lower() or 'whatsapp_number_key' in error_message.lower():
                return Response({
                    'error_code': 'WHATSAPP_EXISTS',
                    'message': 'WhatsApp number already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'phone_number' in error_message.lower() or 'phone_number_key' in error_message.lower():
                return Response({
                    'error_code': 'PHONE_EXISTS',
                    'message': 'Phone number already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'username' in error_message.lower():
                return Response({
                    'error_code': 'USERNAME_EXISTS',
                    'message': 'Username already taken',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            elif 'email' in error_message.lower():
                return Response({
                    'error_code': 'EMAIL_EXISTS',
                    'message': 'Email already registered',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            else:
                logger.error(f'Database integrity error: {str(e)}', exc_info=True)
                return Response({
                    'error_code': 'DUPLICATE_ENTRY',
                    'message': 'A record with this information already exists',
                    'status_code': 409
                }, status=status.HTTP_409_CONFLICT)
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f'Admin customer creation error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to create customer',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

