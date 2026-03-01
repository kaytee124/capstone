import logging
from datetime import datetime, date
from decimal import Decimal
from django.db.models import Q, Sum, Count, Min, Max, Avg
from django.db import connection
from django.utils import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from accounts.mixins import AutoRefreshTokenMixin
from accounts.permissions import IsAdminOrSuperadmin
from orders.models import Order
from customers.models import Customer
from payments.models import Payment
from accounts.models import User
from .serializers import (
    SuperadminDashboardSerializer,
    AdminDashboardSerializer,
    EmployeeDashboardSerializer,
    ClientDashboardSerializer,
    RecentOrderSerializer
)

logger = logging.getLogger(__name__)


class DashboardMetricsView(AutoRefreshTokenMixin, APIView):
    """Get role-based dashboard metrics"""
    permission_classes = [IsAuthenticated]
    
    def get_authenticators(self):
        """Allow unauthenticated access for HTML requests, require auth for API"""
        # Check if this is an API request (explicitly requests JSON)
        accept_header = self.request.META.get('HTTP_ACCEPT', '')
        # Only require authentication if explicitly requesting JSON
        if accept_header and 'application/json' in accept_header and 'text/html' not in accept_header:
            return super().get_authenticators()
        # For all other cases (HTML, no header, etc.), allow unauthenticated
        return []
    
    def get_permissions(self):
        """Allow unauthenticated access for HTML requests, require auth for API"""
        # Check if this is an API request (explicitly requests JSON)
        accept_header = self.request.META.get('HTTP_ACCEPT', '')
        # Only require authentication if explicitly requesting JSON
        if accept_header and 'application/json' in accept_header and 'text/html' not in accept_header:
            return [IsAuthenticated()]
        # For all other cases (HTML, no header, etc.), allow unauthenticated
        return [AllowAny()]
    
    def get(self, request, *args, **kwargs):
        """Get dashboard metrics based on user role"""
        try:
            # Check if this is an API request (explicitly requests JSON)
            accept_header = request.META.get('HTTP_ACCEPT', '')
            is_api_request = accept_header and 'application/json' in accept_header and 'text/html' not in accept_header
            
            # If not an API request, render HTML template
            if not is_api_request:
                # Render template without requiring authentication
                # The JavaScript will use token from localStorage to fetch data
                return render(request, 'dashboard/dashboard.html')
            
            # For API requests, require authentication
            if not request.user.is_authenticated:
                return Response({
                    'error_code': 'NO_TOKEN',
                    'message': 'Authentication credentials not provided',
                    'status_code': 401
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            today = timezone.now().date()
            
            # Get metrics based on role
            if user.role == 'superadmin':
                data = self._get_superadmin_metrics(user, today)
                serializer = SuperadminDashboardSerializer(data=data)
            elif user.role == 'admin':
                data = self._get_admin_metrics(user, today)
                serializer = AdminDashboardSerializer(data=data)
            elif user.role == 'employee':
                data = self._get_employee_metrics(user, today)
                serializer = EmployeeDashboardSerializer(data=data)
            elif user.role == 'client':
                data = self._get_client_metrics(user, today)
                serializer = ClientDashboardSerializer(data=data)
            else:
                return Response({
                    'error_code': 'INVALID_ROLE',
                    'message': 'Invalid user role',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate the data
            serializer.is_valid(raise_exception=True)
            return Response({
                'status': 'success',
                'data': serializer.validated_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Dashboard metrics error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to retrieve dashboard metrics',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_superadmin_metrics(self, user, today):
        """Get metrics for superadmin"""
        total_customers = User.objects.filter(role='client').count()
        total_staff = User.objects.filter(role__in=['admin', 'employee']).count()
        total_orders = Order.objects.count()
        # Total revenue should be sum of amount_paid (actual payments received)
        total_revenue = Order.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        today_orders = Order.objects.filter(created_at__date=today).count()
        # Today's revenue should be sum of amount_paid for today's orders
        today_revenue = Order.objects.filter(created_at__date=today).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        pending_orders = Order.objects.filter(order_status='pending').count()
        in_progress_orders = Order.objects.filter(order_status='in_progress').count()
        ready_for_pickup = Order.objects.filter(order_status='ready').count()
        
        # Calculate total outstanding (sum of (total_amount - amount_paid) for unpaid orders)
        unpaid_orders = Order.objects.filter(~Q(payment_status='paid'))
        total_outstanding = Decimal('0')
        for order in unpaid_orders:
            total_outstanding += (order.total_amount - order.amount_paid)
        
        # Get recent orders (last 10)
        recent_orders_qs = Order.objects.select_related(
            'customer__user'
        ).order_by('-created_at')[:10]
        
        recent_orders = []
        for order in recent_orders_qs:
            customer_name = None
            if order.customer and order.customer.user:
                customer_name = f"{order.customer.user.first_name} {order.customer.user.last_name}".strip()
            
            recent_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': customer_name,
                'total_amount': order.total_amount,
                'status': order.order_status
            })
        
        return {
            'total_customers': total_customers,
            'total_staff': total_staff,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'today_orders': today_orders,
            'today_revenue': today_revenue,
            'pending_orders': pending_orders,
            'in_progress_orders': in_progress_orders,
            'ready_for_pickup': ready_for_pickup,
            'total_outstanding': total_outstanding,
            'recent_orders': recent_orders
        }
    
    def _get_admin_metrics(self, user, today):
        """Get metrics for admin"""
        total_customers = User.objects.filter(role='client').count()
        total_orders = Order.objects.count()
        # Total revenue should be sum of amount_paid (actual payments received)
        total_revenue = Order.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        today_orders = Order.objects.filter(created_at__date=today).count()
        # Today's revenue should be sum of amount_paid for today's orders
        today_revenue = Order.objects.filter(created_at__date=today).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        pending_orders = Order.objects.filter(order_status='pending').count()
        ready_for_pickup = Order.objects.filter(order_status='ready').count()
        
        # Get recent orders (last 10)
        recent_orders_qs = Order.objects.select_related(
            'customer__user'
        ).order_by('-created_at')[:10]
        
        recent_orders = []
        for order in recent_orders_qs:
            customer_name = None
            if order.customer and order.customer.user:
                customer_name = f"{order.customer.user.first_name} {order.customer.user.last_name}".strip()
            
            recent_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': customer_name,
                'total_amount': order.total_amount,
                'status': order.order_status
            })
        
        return {
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'today_orders': today_orders,
            'today_revenue': today_revenue,
            'pending_orders': pending_orders,
            'ready_for_pickup': ready_for_pickup,
            'recent_orders': recent_orders
        }
    
    def _get_employee_metrics(self, user, today):
        """Get metrics for employee"""
        my_orders = Order.objects.filter(assigned_to=user).count()
        my_pending = Order.objects.filter(assigned_to=user, order_status='pending').count()
        my_in_progress = Order.objects.filter(assigned_to=user, order_status='in_progress').count()
        my_today_orders = Order.objects.filter(assigned_to=user, created_at__date=today).count()
        my_revenue = Order.objects.filter(assigned_to=user).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Get assigned orders
        assigned_orders_qs = Order.objects.filter(
            assigned_to=user
        ).select_related(
            'customer__user'
        ).order_by('-created_at')[:10]
        
        my_assigned_orders = []
        for order in assigned_orders_qs:
            customer_name = None
            if order.customer and order.customer.user:
                customer_name = f"{order.customer.user.first_name} {order.customer.user.last_name}".strip()
            
            my_assigned_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': customer_name,
                'status': order.order_status,
                'estimated_completion': order.estimated_completion_date
            })
        
        return {
            'my_orders': my_orders,
            'my_pending': my_pending,
            'my_in_progress': my_in_progress,
            'my_today_orders': my_today_orders,
            'my_revenue': my_revenue,
            'my_assigned_orders': my_assigned_orders
        }
    
    def _get_client_metrics(self, user, today):
        """Get metrics for client"""
        try:
            customer = Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            return {
                'total_orders': 0,
                'total_spent': Decimal('0'),
                'pending_orders': 0,
                'ready_for_pickup': 0,
                'recent_orders': []
            }
        
        total_orders = Order.objects.filter(customer=customer).count()
        # Total spent should be sum of amount_paid (actual payments made)
        total_spent = Order.objects.filter(customer=customer).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        pending_orders = Order.objects.filter(customer=customer, order_status='pending').count()
        ready_for_pickup = Order.objects.filter(customer=customer, order_status='ready').count()
        
        # Get recent orders (last 10)
        recent_orders_qs = Order.objects.filter(
            customer=customer
        ).order_by('-created_at')[:10]
        
        recent_orders = []
        for order in recent_orders_qs:
            balance = order.total_amount - order.amount_paid
            recent_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': order.total_amount,
                'balance': balance,
                'status': order.order_status,
                'created_at': order.created_at.date() if order.created_at else None
            })
        
        return {
            'total_orders': total_orders,
            'total_spent': total_spent,
            'pending_orders': pending_orders,
            'ready_for_pickup': ready_for_pickup,
            'recent_orders': recent_orders
        }


class RevenueReportView(AutoRefreshTokenMixin, APIView):
    """Get revenue report for date range"""
    permission_classes = [IsAuthenticated, IsAdminOrSuperadmin]
    
    def get(self, request, *args, **kwargs):
        """Get revenue report"""
        try:
            # Validate permissions
            if request.user.role not in ['admin', 'superadmin']:
                return Response({
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Only admins and superadmins can view revenue reports',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            group_by = request.query_params.get('group_by', 'day')
            
            # Validate required parameters
            if not start_date_str or not end_date_str:
                return Response({
                    'error_code': 'MISSING_DATES',
                    'message': 'Start date and end date are required',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error_code': 'INVALID_DATE_FORMAT',
                    'message': 'Dates must be in YYYY-MM-DD format',
                    'status_code': 422
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            # Validate date range
            if end_date < start_date:
                return Response({
                    'error_code': 'INVALID_DATE_RANGE',
                    'message': 'End date must be after start date',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get revenue data
            payments = Payment.objects.filter(
                status='success',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).select_related('created_by', 'order')
            
            # Calculate summary
            summary = payments.aggregate(
                unique_orders=Count('order_id', distinct=True),
                total_transactions=Count('id'),
                grand_total=Sum('amount'),
                min_transaction=Min('amount'),
                max_transaction=Max('amount'),
                average_transaction=Avg('amount')
            )
            
            # Get daily breakdown
            daily_breakdown = []
            if group_by == 'day':
                # Group by date and payment method
                from django.db.models.functions import TruncDate
                from django.db.models import F
                
                payment_groups = payments.values(
                    date=TruncDate('created_at'),
                    payment_method=F('payment_method')
                ).annotate(
                    transaction_count=Count('id'),
                    total_amount=Sum('amount')
                ).order_by('-date', 'payment_method')
                
                for group in payment_groups:
                    daily_breakdown.append({
                        'date': group['date'].strftime('%Y-%m-%d'),
                        'payment_method': group['payment_method'],
                        'transaction_count': group['transaction_count'],
                        'total_amount': group['total_amount']
                    })
            elif group_by == 'week':
                # Group by week
                from django.db.models.functions import TruncWeek
                payment_groups = payments.values(
                    week=TruncWeek('created_at')
                ).annotate(
                    transaction_count=Count('id'),
                    total_amount=Sum('amount')
                ).order_by('-week')
                
                for group in payment_groups:
                    daily_breakdown.append({
                        'date': group['week'].strftime('%Y-%m-%d'),
                        'payment_method': 'all',
                        'transaction_count': group['transaction_count'],
                        'total_amount': group['total_amount']
                    })
            elif group_by == 'month':
                # Group by month
                from django.db.models.functions import TruncMonth
                payment_groups = payments.values(
                    month=TruncMonth('created_at')
                ).annotate(
                    transaction_count=Count('id'),
                    total_amount=Sum('amount')
                ).order_by('-month')
                
                for group in payment_groups:
                    daily_breakdown.append({
                        'date': group['month'].strftime('%Y-%m-%d'),
                        'payment_method': 'all',
                        'transaction_count': group['transaction_count'],
                        'total_amount': group['total_amount']
                    })
            
            return Response({
                'status': 'success',
                'data': {
                    'summary': {
                        'unique_orders': summary['unique_orders'] or 0,
                        'total_transactions': summary['total_transactions'] or 0,
                        'grand_total': str(summary['grand_total'] or Decimal('0')),
                        'min_transaction': str(summary['min_transaction'] or Decimal('0')),
                        'max_transaction': str(summary['max_transaction'] or Decimal('0')),
                        'average_transaction': str(summary['average_transaction'] or Decimal('0'))
                    },
                    'daily_breakdown': daily_breakdown
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Revenue report error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to generate revenue report',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
