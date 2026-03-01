from django.db import models
from orders.models import Order
from accounts.models import User

# Create your models here.

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.RESTRICT, db_column='order_id')
    reference = models.CharField(max_length=100, unique=True, db_column='reference')
    amount = models.DecimalField(max_digits=12, decimal_places=2, db_column='amount')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('abandoned', 'Abandoned')],
        default='pending',
        db_column='status'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[('paystack', 'Paystack'), ('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('ussd', 'USSD')],
        db_column='payment_method'
    )
    transaction_id = models.CharField(max_length=100, null=True, blank=True, db_column='transaction_id')
    payer_phone = models.CharField(max_length=20, null=True, blank=True, db_column='payer_phone')
    currency = models.CharField(max_length=3, default='GHS', db_column='currency')
    fees = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='fees')
    metadata = models.JSONField(default=dict, null=True, blank=True, db_column='metadata')
    verified_at = models.DateTimeField(null=True, blank=True, db_column='verified_at')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_created', db_column='created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_updated', db_column='updated_by')

    def __str__(self):
        return f"Payment {self.reference} - {self.amount}"

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']