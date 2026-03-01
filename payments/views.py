import requests
import logging
import uuid
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from accounts.mixins import AutoRefreshTokenMixin
from orders.models import Order
from customers.models import Customer
from .models import Payment
from .serializers import PaymentInitializeSerializer
import json

logger = logging.getLogger(__name__)


class PaymentInitializeView(AutoRefreshTokenMixin, APIView):
    """Initialize a Paystack payment transaction"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # Only clients can make payments
            if user.role != 'client':
                return Response({
                    'error_code': 'PERMISSION_DENIED',
                    'message': 'Only clients can make payments',
                    'status_code': 403
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = PaymentInitializeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            order_id = serializer.validated_data['order_id']
            
            # Get the order
            try:
                customer = Customer.objects.get(user=user)
                order = Order.objects.select_related('customer__user').get(id=order_id, customer=customer)
            except Order.DoesNotExist:
                return Response({
                    'error_code': 'ORDER_NOT_FOUND',
                    'message': 'Order not found or you do not have permission to pay for this order',
                    'status_code': 404
                }, status=status.HTTP_404_NOT_FOUND)
            except Customer.DoesNotExist:
                return Response({
                    'error_code': 'CUSTOMER_NOT_FOUND',
                    'message': 'Customer profile not found',
                    'status_code': 404
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get payment amount from request
            payment_amount = Decimal(str(serializer.validated_data.get('amount', 0)))
            
            # Check if order is already fully paid
            if order.payment_status == 'paid':
                return Response({
                    'error_code': 'ORDER_ALREADY_PAID',
                    'message': 'This order has already been fully paid',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate amount to pay (remaining balance)
            remaining_amount = order.total_amount - order.amount_paid
            if remaining_amount <= 0:
                return Response({
                    'error_code': 'NO_AMOUNT_DUE',
                    'message': 'No amount due for this order',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate payment amount doesn't exceed remaining balance
            if payment_amount > remaining_amount:
                return Response({
                    'error_code': 'AMOUNT_EXCEEDS_BALANCE',
                    'message': f'Payment amount (GHS {payment_amount:.2f}) cannot exceed remaining balance (GHS {remaining_amount:.2f})',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get customer email
            customer_email = order.customer.user.email
            if not customer_email:
                return Response({
                    'error_code': 'EMAIL_NOT_FOUND',
                    'message': 'Customer email not found. Please update your profile.',
                    'status_code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert amount to pesewas (Paystack uses smallest currency unit - 100 pesewas = 1 GHS)
            amount_in_pesewas = int(payment_amount * 100)
            
            # Generate unique reference for this payment attempt
            # Format: PAY-{order_id}-{uuid} to ensure uniqueness while keeping order context
            unique_ref = f"PAY-{order.id}-{uuid.uuid4().hex[:12].upper()}"
            
            # Create payment record first (before calling Paystack)
            # This ensures we have a record even if Paystack call fails
            with transaction.atomic():
                payment = Payment.objects.create(
                    order=order,
                    reference=unique_ref,
                    amount=payment_amount,  # Use customer-provided amount
                    status='pending',
                    payment_method='paystack',
                    transaction_id=unique_ref,  # Will be updated after Paystack response
                    currency='GHS',
                    metadata={
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'customer_id': customer.id
                    },
                    created_by=user
                )
            
            # Prepare Paystack API request
            paystack_url = 'https://api.paystack.co/transaction/initialize'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'email': customer_email,
                'amount': str(amount_in_pesewas),
                'reference': unique_ref,
                'callback_url': settings.PAYSTACK_CALLBACK_URL,
                'channels': ['bank', 'card', 'apple_pay', 'mobile_money'],
                'metadata': {
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_id': customer.id,
                    'payment_id': payment.id
                }
            }
            
            # Make request to Paystack
            response = requests.post(paystack_url, headers=headers, json=payload, timeout=30)
            response_data = response.json()
            
            if not response.ok or not response_data.get('status'):
                logger.error(f'Paystack API error: {response_data}')
                # Update payment status to failed
                payment.status = 'failed'
                payment.metadata = {
                    **payment.metadata,
                    'paystack_error': response_data,
                    'error_message': response_data.get('message', 'Failed to initialize payment')
                }
                payment.save()
                return Response({
                    'error_code': 'PAYSTACK_ERROR',
                    'message': response_data.get('message', 'Failed to initialize payment'),
                    'status_code': 500
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Update payment record with Paystack response data
            payment_data = response_data.get('data', {})
            access_code = payment_data.get('access_code')
            authorization_url = payment_data.get('authorization_url')
            
            payment.transaction_id = access_code or unique_ref
            payment.metadata = {
                **payment.metadata,
                'paystack_response': response_data,
                'access_code': access_code,
                'authorization_url': authorization_url
            }
            payment.save()
            
            return Response({
                'status': 'success',
                'message': 'Payment initialized successfully',
                'data': {
                    'authorization_url': authorization_url,
                    'access_code': access_code,
                    'reference': unique_ref,
                    'payment_id': payment.id
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Payment initialization error: {str(e)}', exc_info=True)
            return Response({
                'error_code': 'SERVER_ERROR',
                'message': 'Failed to initialize payment',
                'status_code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCallbackView(APIView):
    """Handle Paystack payment callback and verify transaction"""
    permission_classes = []  # No authentication required for callback
    
    def get(self, request, *args, **kwargs):
        try:
            reference = request.GET.get('reference')
            
            if not reference:
                return render(request, 'payments/payment_callback.html', {
                    'success': False,
                    'message': 'Payment reference not provided'
                })
            
            # Verify transaction with Paystack
            paystack_url = f'https://api.paystack.co/transaction/verify/{reference}'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
            }
            
            response = requests.get(paystack_url, headers=headers, timeout=30)
            response_data = response.json()
            
            if not response.ok or not response_data.get('status'):
                logger.error(f'Paystack verification error: {response_data}')
                return render(request, 'payments/payment_callback.html', {
                    'success': False,
                    'message': response_data.get('message', 'Failed to verify payment')
                })
            
            transaction_data = response_data.get('data', {})
            transaction_status = transaction_data.get('status')
            transaction_amount = Decimal(str(transaction_data.get('amount', 0))) / 100  # Convert from pesewas
            
            # Get payment record
            try:
                payment = Payment.objects.select_related('order').get(reference=reference)
                order = payment.order
            except Payment.DoesNotExist:
                logger.error(f'Payment not found for reference: {reference}')
                return render(request, 'payments/payment_callback.html', {
                    'success': False,
                    'message': 'Payment record not found'
                })
            
            # Verify amount matches the payment record amount (customer-provided amount)
            expected_amount = payment.amount
            if abs(transaction_amount - expected_amount) > Decimal('0.01'):  # Allow 1 pesewa difference
                logger.warning(f'Amount mismatch for payment {reference}. Expected: {expected_amount}, Got: {transaction_amount}')
                payment.status = 'failed'
                payment.metadata = {
                    **payment.metadata,
                    'verification_error': 'Amount mismatch',
                    'expected_amount': str(expected_amount),
                    'received_amount': str(transaction_amount)
                }
                payment.save()
                return render(request, 'payments/payment_callback.html', {
                    'success': False,
                    'message': 'Payment amount mismatch. Please contact support.'
                })
            
            # Update payment record
            with transaction.atomic():
                if transaction_status == 'success':
                    payment.status = 'success'
                    payment.transaction_id = str(transaction_data.get('id', ''))
                    payment.fees = Decimal(str(transaction_data.get('fees', 0))) / 100
                    # Parse paid_at timestamp if available
                    paid_at_str = transaction_data.get('paid_at')
                    if paid_at_str:
                        try:
                            payment.verified_at = datetime.fromisoformat(paid_at_str.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            payment.verified_at = timezone.now()
                    else:
                        payment.verified_at = timezone.now()
                    payment.metadata = {
                        **payment.metadata,
                        'verification_response': response_data,
                        'channel': transaction_data.get('channel'),
                        'gateway_response': transaction_data.get('gateway_response')
                    }
                    payment.save()
                    
                    # Update order payment status
                    # The database trigger will handle amount_paid and payment_status updates
                    # But we'll also update it here to ensure consistency
                    from django.db.models import Sum
                    total_paid = Payment.objects.filter(
                        order=order,
                        status='success'
                    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                    
                    # Ensure amount_paid never exceeds total_amount (to satisfy constraint)
                    order.amount_paid = min(total_paid, order.total_amount)
                    if order.amount_paid >= order.total_amount:
                        order.payment_status = 'paid'
                    elif order.amount_paid > 0:
                        order.payment_status = 'partially_paid'
                    else:
                        order.payment_status = 'pending'
                    order.save()
                    
                    # Render callback template with order_id for client-side redirect
                    # This allows the browser to use tokens from localStorage
                    return render(request, 'payments/payment_callback.html', {
                        'success': True,
                        'message': 'Payment processed successfully',
                        'order_id': order.id
                    })
                else:
                    payment.status = 'failed'
                    payment.metadata = {
                        **payment.metadata,
                        'verification_response': response_data,
                        'gateway_response': transaction_data.get('gateway_response', 'Payment failed')
                    }
                    payment.save()
                    
                    return render(request, 'payments/payment_callback.html', {
                        'success': False,
                        'message': transaction_data.get('gateway_response', 'Payment failed')
                    })
                    
        except Exception as e:
            logger.error(f'Payment callback error: {str(e)}', exc_info=True)
            return render(request, 'payments/payment_callback.html', {
                'success': False,
                'message': 'An error occurred while processing your payment. Please contact support.'
            })
