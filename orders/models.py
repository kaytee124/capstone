from django.db import models
from customers.models import Customer
from accounts.models import User
from services.models import Service

# Create your models here.
class Order(models.Model):
    order_number = models.CharField(max_length=50, unique=True, db_column='order_number')
    customer = models.ForeignKey(Customer, on_delete=models.RESTRICT, db_column='customer_id')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='assigned_to')
    order_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'), 
            ('in_progress', 'In Progress'), 
            ('ready', 'Ready'), 
            ('completed', 'Completed'), 
            ('cancelled', 'Cancelled')
        ],
        default='pending',
        db_column='order_status'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'), 
            ('partially_paid', 'Partially Paid'), 
            ('paid', 'Paid')
        ],
        default='pending',
        db_column='payment_status'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='total_amount')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='amount_paid')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='discount_amount')
    delivery_notes = models.TextField(blank=True, null=True, db_column='delivery_notes')
    special_instructions = models.TextField(blank=True, null=True, db_column='special_instructions')
    pickup_date = models.DateField(null=True, blank=True, db_column='pickup_date')
    delivery_date = models.DateField(null=True, blank=True, db_column='delivery_date')
    estimated_completion_date = models.DateField(null=True, blank=True, db_column='estimated_completion_date')
    completed_at = models.DateTimeField(null=True, blank=True, db_column='completed_at')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_created', db_column='created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_updated', db_column='updated_by')

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.user.username}"

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', db_column='order_id')
    service = models.ForeignKey(Service, on_delete=models.RESTRICT, db_column='service_id')
    item_name = models.CharField(max_length=100, db_column='item_name')
    description = models.TextField(blank=True, null=True, db_column='description')
    quantity = models.IntegerField(default=1, db_column='quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='unit_price')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, db_column='subtotal')
    notes = models.TextField(blank=True, null=True, db_column='notes')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    def __str__(self):
        return f"{self.item_name} x{self.quantity} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate subtotal if not set
        if not self.subtotal:
            self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['created_at']