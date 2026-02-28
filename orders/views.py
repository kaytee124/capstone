from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied, ValidationError, NotFound
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from accounts.permissions import IsAdminOrSuperadmin, IsStaff
from .models import Order
from .serializers import OrderSerializer
from customers.models import Customer
import logging

logger = logging.getLogger(__name__)

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        """Render order list template or return JSON data"""
        # Check if this is an HTML request (template rendering)
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'text/html' in accept_header or not accept_header:
            # All authenticated users can view orders (with different filters)
            return render(request, 'orders/order_list.html')
        # For API requests, return JSON
        return self._get_orders_json(request)
    
    def _get_orders_json(self, request):
        """Get list of orders with role-based filtering"""
        try:
            user = request.user
            
            # Staff (admin, superadmin, employee) can see all orders
            if user.role in ['admin', 'superadmin', 'employee']:
                queryset = Order.objects.all().select_related('customer__user', 'assigned_to', 'created_by')
            # Clients can only see their own orders
            elif user.role == 'client':
                try:
                    customer = Customer.objects.get(user=user)
                    queryset = Order.objects.filter(customer=customer).select_related('customer__user', 'assigned_to', 'created_by')
                except Customer.DoesNotExist:
                    queryset = Order.objects.none()
            else:
                queryset = Order.objects.none()
            
            # Apply filters
            order_status = request.query_params.get('order_status')
            if order_status:
                queryset = queryset.filter(order_status=order_status)
            
            payment_status = request.query_params.get('payment_status')
            if payment_status:
                queryset = queryset.filter(payment_status=payment_status)
            
            # Order by most recent first
            queryset = queryset.order_by('-created_at')
            
            serializer = self.serializer_class(queryset, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Failed to get orders: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve orders',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        """Render order creation form"""
        # Check if user has permission to create orders
        if request.user.role not in ['admin', 'superadmin', 'employee']:
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only admins, superadmins, and staff can create orders',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        
        return render(request, 'orders/order_create.html')
    
    def post(self, request, *args, **kwargs):
        """Create a new order with order items - only admin, superadmin, and staff can create"""
        try:
            user = request.user
            
            # Check if user has permission to create orders
            if user.role not in ['admin', 'superadmin', 'employee']:
                return Response({
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Only admins, superadmins, and staff can create orders',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            # For employees: automatically set assigned_to to the employee creating the order
            # if not already set
            if user.role == 'employee':
                if 'assigned_to' not in request.data or not request.data.get('assigned_to'):
                    request.data['assigned_to'] = user.id
            
            # Pass user in context so serializer can set created_by
            serializer = self.serializer_class(
                data=request.data,
                context={'user': user}
            )
            serializer.is_valid(raise_exception=True)
            order = serializer.save()
            
            # Return the created order with items
            order_data = self.serializer_class(order).data
            
            return Response({
                'status': 'success',
                'message': 'Order created successfully',
                'data': order_data
            }, status=status.HTTP_201_CREATED)
            
        except (NotAuthenticated, AuthenticationFailed) as e:
            return Response({
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except (InvalidToken, TokenError) as e:
            return Response({
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except PermissionDenied as e:
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only admins, superadmins, and staff can create orders',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
            
        except ValidationError as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                field_errors = []
                for field, errors in error_detail.items():
                    if isinstance(errors, list) and len(errors) > 0:
                        error_msg = errors[0]
                        if hasattr(error_msg, 'string'):
                            msg = error_msg.string
                        elif isinstance(error_msg, str):
                            msg = error_msg
                        else:
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
            
            return Response({
                'error_code': 'VALIDATION_ERROR',
                'message': 'Validation failed. Please check your input.',
                'status_code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f'Failed to create order: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to create order',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        """Render order update form"""
        order_id = kwargs.get('id')
        user = request.user
        
        # Check if user has permission to update orders (staff only)
        if user.role not in ['admin', 'superadmin', 'employee']:
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only staff can update orders',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if order exists
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({
                'error_code': 'ORDER_NOT_FOUND',
                'message': 'Order not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        return render(request, 'orders/order_update.html', {'order_id': order_id})
    
    def put(self, request, *args, **kwargs):
        """Update an existing order - staff can update, but not amount_paid"""
        order_id = kwargs.get('id')
        try:
            user = request.user
            
            # Check if user has permission to update orders
            if user.role not in ['admin', 'superadmin', 'employee']:
                return Response({
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Only staff can update orders',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the order
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({
                    'error_code': 'ORDER_NOT_FOUND',
                    'message': 'Order not found',
                    'status_code': 404
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Remove amount_paid from request data if present (not allowed to update)
            request_data = request.data.copy()
            if 'amount_paid' in request_data:
                del request_data['amount_paid']
            
            # Pass user in context so serializer can set updated_by
            serializer = self.serializer_class(
                order,
                data=request_data,
                partial=True,
                context={'user': user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Return the updated order
            order_data = self.serializer_class(order).data
            
            return Response({
                'status': 'success',
                'message': 'Order updated successfully',
                'data': order_data
            }, status=status.HTTP_200_OK)
            
        except (NotAuthenticated, AuthenticationFailed) as e:
            return Response({
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except (InvalidToken, TokenError) as e:
            return Response({
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except PermissionDenied as e:
            return Response({
                'error_code': 'INSUFFICIENT_PERMISSIONS',
                'message': 'Only staff can update orders',
                'status_code': 403
            }, status=status.HTTP_403_FORBIDDEN)
            
        except ValidationError as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                field_errors = []
                for field, errors in error_detail.items():
                    if isinstance(errors, list) and len(errors) > 0:
                        error_msg = errors[0]
                        if hasattr(error_msg, 'string'):
                            msg = error_msg.string
                        elif isinstance(error_msg, str):
                            msg = error_msg
                        else:
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
            
            return Response({
                'error_code': 'VALIDATION_ERROR',
                'message': 'Validation failed. Please check your input.',
                'status_code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f'Failed to update order: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to update order',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        """Get an existing order by id - with role-based access control"""
        order_id = kwargs.get('id')
        try:
            # Use prefetch_related to include order items
            order = Order.objects.prefetch_related('order_items__service').select_related('customer__user', 'assigned_to', 'created_by').get(id=order_id)
            user = request.user
            
            # Check access permissions
            # Staff can see all orders
            if user.role in ['admin', 'superadmin', 'employee']:
                pass  # Allow access
            # Clients can only see their own orders
            elif user.role == 'client':
                try:
                    customer = Customer.objects.get(user=user)
                    if order.customer != customer:
                        return Response({
                            'error_code': 'PERMISSION_DENIED',
                            'message': 'You can only view your own orders',
                            'status_code': 403
                        }, status=status.HTTP_403_FORBIDDEN)
                except Customer.DoesNotExist:
                    return Response({
                        'error_code': 'PERMISSION_DENIED',
                        'message': 'Customer profile not found',
                        'status_code': 403
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'error_code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission to view this order',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if this is an HTML request (template rendering)
            accept_header = request.META.get('HTTP_ACCEPT', '')
            if 'text/html' in accept_header or not accept_header:
                return render(request, 'orders/order_detail.html', {'order_id': order_id})
            
            # For API requests, return JSON
            serializer = self.serializer_class(order)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response({
                'error_code': 'ORDER_NOT_FOUND',
                'message': 'Order not found',
                'status_code': 404
            }, status=status.HTTP_404_NOT_FOUND)
            
        except (NotAuthenticated, AuthenticationFailed) as e:
            return Response({
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except (InvalidToken, TokenError) as e:
            return Response({
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            logger.error(f'Failed to get order: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve order',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
