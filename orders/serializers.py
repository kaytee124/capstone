from rest_framework import serializers
from .models import Order, OrderItem
from customers.models import Customer
from accounts.models import User
from services.models import Service
import uuid
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'service_id', 'service_name', 'item_name', 'description', 'quantity', 'unit_price', 'subtotal', 'notes', 'created_at', 'updated_at']
        read_only_fields = ('id', 'created_at', 'updated_at', 'subtotal')
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative")
        return value

class OrderSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.user.username', read_only=True)
    customer_name = serializers.SerializerMethodField()
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    customer_id = serializers.IntegerField(write_only=True, required=True)
    order_items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completed_at', 'order_number', 'amount_paid', 'customer')
        extra_kwargs = {
            'order_status': {'required': False},
            'payment_status': {'required': False},
            'amount_paid': {'required': False},
        }
    
    def get_customer_name(self, obj):
        if obj.customer and obj.customer.user:
            return f"{obj.customer.user.first_name} {obj.customer.user.last_name}"
        return None
    
    def validate(self, data):
        # Only validate order items if this is a create operation (order_items_data provided)
        order_items_data = data.get('order_items_data', [])
        if order_items_data:
            if not order_items_data:
                raise serializers.ValidationError("At least one order item is required")
            
            # Calculate total amount from items
            total = Decimal('0.00')
            for item_data in order_items_data:
                quantity = Decimal(str(item_data.get('quantity', 1)))
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
                subtotal = quantity * unit_price
                total += subtotal
            
            # Set total_amount if not provided
            if 'total_amount' not in data or not data['total_amount']:
                data['total_amount'] = total - Decimal(str(data.get('discount_amount', 0)))
        
        return data
    
    def create(self, validated_data):
        # Extract order items data
        order_items_data = validated_data.pop('order_items_data', [])
        customer_id = validated_data.pop('customer_id', None)
        
        # Validate customer_id
        if not customer_id:
            raise serializers.ValidationError({'customer_id': 'Customer is required'})
        
        # Get customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({'customer_id': 'Customer not found'})
        except (ValueError, TypeError):
            raise serializers.ValidationError({'customer_id': 'Invalid customer ID'})
        
        validated_data['customer'] = customer
        
        # Generate unique order number
        if not validated_data.get('order_number'):
            validated_data['order_number'] = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Set created_by from context
        user = self.context.get('user')
        if user:
            validated_data['created_by'] = user
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        total_amount = Decimal('0.00')
        for item_data in order_items_data:
            service_id = item_data.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                raise serializers.ValidationError({'order_items_data': f'Service with id {service_id} not found'})
            
            quantity = item_data.get('quantity', 1)
            unit_price = Decimal(str(item_data.get('unit_price', service.price)))
            subtotal = quantity * unit_price
            total_amount += subtotal
            
            OrderItem.objects.create(
                order=order,
                service=service,
                item_name=item_data.get('item_name', service.name),
                description=item_data.get('description', service.description),
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                notes=item_data.get('notes', '')
            )
        
        # Update order total (subtract discount if any)
        discount = Decimal(str(validated_data.get('discount_amount', 0)))
        order.total_amount = total_amount - discount
        order.save()
        
        return order
    
    def update(self, instance, validated_data):
        """Update order with updated_by from context"""
        user = self.context.get('user')
        
        # Remove order_items_data if present (not updating items in this method)
        validated_data.pop('order_items_data', None)
        validated_data.pop('customer_id', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Set updated_by
        instance.updated_by = user
        instance.save()
        
        return instance