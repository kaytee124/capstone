from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class PaymentInitializeSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    
    def validate_order_id(self, value):
        if value <= 0:
            raise serializers.ValidationError("Order ID must be a positive integer")
        return value
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0")
        return value