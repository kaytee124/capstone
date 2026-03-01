from rest_framework import serializers

class RecentOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_number = serializers.CharField()
    customer_name = serializers.CharField(required=False, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    status = serializers.CharField()
    estimated_completion = serializers.DateField(required=False, allow_null=True)
    created_at = serializers.DateField(required=False, allow_null=True)

class SuperadminDashboardSerializer(serializers.Serializer):
    total_customers = serializers.IntegerField()
    total_staff = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_orders = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    in_progress_orders = serializers.IntegerField()
    ready_for_pickup = serializers.IntegerField()
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    recent_orders = RecentOrderSerializer(many=True, required=False)

class AdminDashboardSerializer(serializers.Serializer):
    total_customers = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_orders = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    ready_for_pickup = serializers.IntegerField()
    recent_orders = RecentOrderSerializer(many=True, required=False)

class EmployeeDashboardSerializer(serializers.Serializer):
    my_orders = serializers.IntegerField()
    my_pending = serializers.IntegerField()
    my_in_progress = serializers.IntegerField()
    my_today_orders = serializers.IntegerField()
    my_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    my_assigned_orders = RecentOrderSerializer(many=True, required=False)

class ClientDashboardSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    ready_for_pickup = serializers.IntegerField()
    recent_orders = RecentOrderSerializer(many=True, required=False)
