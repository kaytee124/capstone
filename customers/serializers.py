from rest_framework import serializers
from .models import Customer
from accounts.models import User

class Customercreationserializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='client'), required=True)
    phone_number = serializers.CharField(required=True)
    whatsapp_number = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    preferred_contact_method = serializers.ChoiceField(choices=[('phone', 'Phone'), ('whatsapp', 'Whatsapp')], required=True)
    notes = serializers.CharField(required=True)
    total_orders = serializers.IntegerField(required=True)
    total_spent = serializers.DecimalField(required=True, max_digits=12, decimal_places=2)
    last_order_date = serializers.DateTimeField(required=True)
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__in=['superadmin', 'admin','employee']), required=True)
    updated_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__in=['superadmin', 'admin','employee']), required=True)
    class Meta:
        model = Customer
        fields = ['id', 'user', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'created_by', 'updated_by']