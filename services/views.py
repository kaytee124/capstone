from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied, ValidationError, NotFound
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from accounts.permissions import IsAdminOrSuperadmin
from .models import Service
from .serializers import ServiceSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class ServiceListView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ServiceSerializer

    def get(self, request, *args, **kwargs):
        """Render services list template or return JSON data"""
        # Check if this is an HTML request (template rendering)
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'text/html' in accept_header or not accept_header:
            # Check if user is admin or superadmin for template access
            if request.user.is_authenticated and (request.user.role in ['admin', 'superadmin']):
                return render(request, 'services/services_list.html')
            # If not authenticated or not admin/superadmin, redirect to login or return 403
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only admins and superadmins can access this page',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        # For API requests, return JSON
        return self._get_services_json(request)
    
    def _get_services_json(self, request):
        """Get list of services with optional filtering"""
        try:
            # Start with all services
            queryset = Service.objects.all()
            
            # Filter by is_active (only if explicitly provided)
            is_active = request.query_params.get('is_active')
            if is_active is not None and is_active != '':
                if is_active.lower() == 'true':
                    queryset = queryset.filter(is_active=True)
                elif is_active.lower() == 'false':
                    queryset = queryset.filter(is_active=False)
            # If is_active is empty or not provided, show all (no filter)
            
            # Filter by category
            category = request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__icontains=category)
            
            # Search in name and description
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )
            
            # Serialize the queryset
            serializer = self.serializer_class(queryset, many=True)
            
            # Return response in the specified format
            return Response({
                'status': 'success',
                'data': {
                    'count': queryset.count(),
                    'results': serializer.data
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Failed to retrieve services: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve services',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ServiceCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = ServiceSerializer

    def get(self, request, *args, **kwargs):
        """Render create service template"""
        return render(request, 'services/service_create.html')
    
    def post(self, request, *args, **kwargs):
        """Create a new service"""
        try:
            # Pass user in context so serializer can set created_by
            serializer = self.serializer_class(
                data=request.data,
                context={'user': request.user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'status': 'success',
                'message': 'Service created successfully',
            }, status=status.HTTP_201_CREATED)
            
        except (NotAuthenticated, AuthenticationFailed) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except (InvalidToken, TokenError) as e:
            # Handle invalid token errors
            return Response({
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except PermissionDenied as e:
            # Handle permission errors
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only admins and superadmins can create services',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
            
        except ValidationError as e:
            # Handle validation errors from serializer
            error_detail = e.detail
            
            # Check if it's a custom error format (dict with error_code) - from validate() method
            if isinstance(error_detail, dict) and 'error_code' in error_detail:
                error_code = error_detail.get('error_code')
                error_message = error_detail.get('message', 'Validation error')
                status_code = error_detail.get('status_code', 400)
                
                # Map status codes
                http_status = status.HTTP_400_BAD_REQUEST
                if status_code == 409:
                    http_status = status.HTTP_409_CONFLICT
                elif status_code == 422:
                    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
                
                return Response({
                    'error_code': error_code,
                    'message': error_message,
                    'status_code': status_code
                }, status=http_status)
            
            # Handle field-level validation errors (from validate_price, validate_name)
            if isinstance(error_detail, dict):
                # Check for price validation error
                if 'price' in error_detail:
                    price_error = error_detail['price']
                    # Could be a list or a dict
                    if isinstance(price_error, list) and len(price_error) > 0:
                        price_error_msg = price_error[0]
                        # Check if it's a dict with error_code
                        if isinstance(price_error_msg, dict) and 'error_code' in price_error_msg:
                            return Response({
                                'error_code': price_error_msg.get('error_code'),
                                'message': price_error_msg.get('message'),
                                'status_code': price_error_msg.get('status_code', 422)
                            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                        # Check if it's a string message about price > 0
                        elif isinstance(price_error_msg, str) and 'greater than 0' in price_error_msg.lower():
                            return Response({
                                'error_code': 'INVALID_PRICE',
                                'message': 'Price must be greater than 0',
                                'status_code': 422
                            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    elif isinstance(price_error, dict) and 'error_code' in price_error:
                        return Response({
                            'error_code': price_error.get('error_code'),
                            'message': price_error.get('message'),
                            'status_code': price_error.get('status_code', 422)
                        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
                # Check for missing required fields
                missing_fields = []
                if 'name' in error_detail:
                    missing_fields.append('name')
                if 'price' in error_detail:
                    missing_fields.append('price')
                
                if missing_fields:
                    return Response({
                        'error_code': 'MISSING_FIELDS',
                        'message': 'Name and price are required',
                        'status_code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generic validation error - format field errors properly
            if isinstance(error_detail, dict):
                field_errors = []
                for field, errors in error_detail.items():
                    if isinstance(errors, list) and len(errors) > 0:
                        # Extract the error message string from ErrorDetail
                        error_msg = errors[0]
                        if hasattr(error_msg, 'string'):
                            # ErrorDetail object - get the string property
                            msg = error_msg.string
                        elif isinstance(error_msg, str):
                            # Already a string
                            msg = error_msg
                        else:
                            # Fallback
                            msg = str(error_msg)
                        
                        field_name = field.replace('_', ' ').title()
                        field_errors.append(f"{field_name}: {msg}")
                    elif isinstance(errors, str):
                        field_name = field.replace('_', ' ').title()
                        field_errors.append(f"{field_name}: {errors}")
                
                if field_errors:
                    return Response({
                        'error_code': 'VALIDATION_ERROR',
                        'message': '. '.join(field_errors),
                        'status_code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fallback for other error formats
            return Response({
                'error_code': 'VALIDATION_ERROR',
                'message': 'Validation failed. Please check your input.',
                'status_code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f'Failed to create service: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to create service',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ServiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = ServiceSerializer

    def get(self, request, *args, **kwargs):
        """Render service detail template or return JSON data"""
        service_id = kwargs.get('id')
        try:
            service = Service.objects.get(id=service_id)
        except (Service.DoesNotExist, ObjectDoesNotExist, ValueError):
            # Check if this is an HTML request
            accept_header = request.META.get('HTTP_ACCEPT', '')
            if 'text/html' in accept_header or not accept_header:
                return render(request, 'services/service_detail.html', {
                    'error': 'Service not found',
                    'service_id': service_id
                })
            return Response({
                'error_code': 'SERVICE_NOT_FOUND',
                'message': 'Service not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if this is an HTML request (template rendering)
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'text/html' in accept_header or not accept_header:
            return render(request, 'services/service_detail.html', {'service_id': service_id})
        # For API requests, return JSON
        serializer = self.serializer_class(service)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class ServiceUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    serializer_class = ServiceSerializer

    def get(self, request, *args, **kwargs):
        """Render update service template"""
        service_id = kwargs.get('id')
        try:
            service = Service.objects.get(id=service_id)
        except (Service.DoesNotExist, ObjectDoesNotExist, ValueError):
            return Response({
                'error_code': 'SERVICE_NOT_FOUND',
                'message': 'Service not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        return render(request, 'services/service_update.html', {'service_id': service_id})
    
    def patch(self, request, *args, **kwargs):
        """Update a service"""
        try:
            # Get service by ID
            try:
                service = Service.objects.get(id=kwargs['id'])
            except (Service.DoesNotExist, ObjectDoesNotExist, ValueError):
                return Response({
                    'error_code': 'SERVICE_NOT_FOUND',
                    'message': 'Service not found',
                    'status_code': 404
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Pass user in context so serializer can set updated_by
            serializer = self.serializer_class(
                service,
                data=request.data,
                partial=True,
                context={'user': request.user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'status': 'success',
                'message': 'Service updated successfully',
            }, status=status.HTTP_200_OK)
            
        except (NotAuthenticated, AuthenticationFailed) as e:
            # Handle authentication errors
            return Response({
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except (InvalidToken, TokenError) as e:
            # Handle invalid token errors
            return Response({
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except PermissionDenied as e:
            # Handle permission errors
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only admins and superadmins can update services',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
            
        except ValidationError as e:
            # Handle validation errors from serializer
            error_detail = e.detail
            
            # Check if it's a custom error format (dict with error_code) - from validate() method
            if isinstance(error_detail, dict) and 'error_code' in error_detail:
                error_code = error_detail.get('error_code')
                error_message = error_detail.get('message', 'Validation error')
                status_code = error_detail.get('status_code', 400)
                
                # Map status codes
                http_status = status.HTTP_400_BAD_REQUEST
                if status_code == 409:
                    http_status = status.HTTP_409_CONFLICT
                elif status_code == 422:
                    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
                
                return Response({
                    'error_code': error_code,
                    'message': error_message,
                    'status_code': status_code
                }, status=http_status)
            
            # Handle field-level validation errors (from validate_price, validate_name)
            if isinstance(error_detail, dict):
                # Check for price validation error
                if 'price' in error_detail:
                    price_error = error_detail['price']
                    # Could be a list or a dict
                    if isinstance(price_error, list) and len(price_error) > 0:
                        price_error_msg = price_error[0]
                        # Check if it's a dict with error_code
                        if isinstance(price_error_msg, dict) and 'error_code' in price_error_msg:
                            return Response({
                                'error_code': price_error_msg.get('error_code'),
                                'message': price_error_msg.get('message'),
                                'status_code': price_error_msg.get('status_code', 422)
                            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                        # Check if it's a string message about price > 0
                        elif isinstance(price_error_msg, str) and 'greater than 0' in price_error_msg.lower():
                            return Response({
                                'error_code': 'INVALID_PRICE',
                                'message': 'Price must be greater than 0',
                                'status_code': 422
                            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    elif isinstance(price_error, dict) and 'error_code' in price_error:
                        return Response({
                            'error_code': price_error.get('error_code'),
                            'message': price_error.get('message'),
                            'status_code': price_error.get('status_code', 422)
                        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
                # Check for missing required fields
                missing_fields = []
                if 'name' in error_detail:
                    missing_fields.append('name')
                if 'price' in error_detail:
                    missing_fields.append('price')
                
                if missing_fields:
                    return Response({
                        'error_code': 'MISSING_FIELDS',
                        'message': 'Name and price are required',
                        'status_code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generic validation error - format field errors properly
            if isinstance(error_detail, dict):
                field_errors = []
                for field, errors in error_detail.items():
                    if isinstance(errors, list) and len(errors) > 0:
                        # Extract the error message string from ErrorDetail
                        error_msg = errors[0]
                        if hasattr(error_msg, 'string'):
                            # ErrorDetail object - get the string property
                            msg = error_msg.string
                        elif isinstance(error_msg, str):
                            # Already a string
                            msg = error_msg
                        else:
                            # Fallback
                            msg = str(error_msg)
                        
                        field_name = field.replace('_', ' ').title()
                        field_errors.append(f"{field_name}: {msg}")
                    elif isinstance(errors, str):
                        field_name = field.replace('_', ' ').title()
                        field_errors.append(f"{field_name}: {errors}")
                
                if field_errors:
                    return Response({
                        'error_code': 'VALIDATION_ERROR',
                        'message': '. '.join(field_errors),
                        'status_code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fallback for other error formats
            return Response({
                'error_code': 'VALIDATION_ERROR',
                'message': 'Validation failed. Please check your input.',
                'status_code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f'Failed to update service: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to update service',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)