from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from customers.models import Customer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by']

class UserByIdSerializer(serializers.ModelSerializer):
    """Serializer for users to get their own profile - returns username, first_name, last_name, email, status, and customer fields if client"""
    status = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_contact_method = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    customer_created_by_name = serializers.SerializerMethodField()
    customer_updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'status', 'updated_by_name', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
        read_only_fields = ['username', 'first_name', 'last_name', 'email', 'status', 'updated_by_name', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'
    
    def get_updated_by_name(self, obj):
        """Get the name of the user who last updated this user"""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None
    
    def get_has_customer_profile(self, obj):
        """Check if user has a customer profile"""
        return hasattr(obj, 'customer_profile')
    
    def get_customer_created_by_name(self, obj):
        """Get the name of the user who created the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.created_by:
            return f"{obj.customer_profile.created_by.first_name} {obj.customer_profile.created_by.last_name}".strip() or obj.customer_profile.created_by.username
        return None
    
    def get_customer_updated_by_name(self, obj):
        """Get the name of the user who last updated the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.updated_by:
            return f"{obj.customer_profile.updated_by.first_name} {obj.customer_profile.updated_by.last_name}".strip() or obj.customer_profile.updated_by.username
        return None
    
    def get_phone_number(self, obj):
        """Get phone number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.phone_number
        return None
    
    def get_whatsapp_number(self, obj):
        """Get whatsapp number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.whatsapp_number
        return None
    
    def get_address(self, obj):
        """Get address from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.address
        return None
    
    def get_preferred_contact_method(self, obj):
        """Get preferred contact method from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.preferred_contact_method
        return None
    
    def get_notes(self, obj):
        """Get notes from customer profile - only if user is a client, show 'no note' if empty"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            notes = obj.customer_profile.notes
            return notes if notes else 'no note'
        return None
    
    def get_total_orders(self, obj):
        """Get total orders from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.total_orders
        return 0
    
    def get_total_spent(self, obj):
        """Get total spent from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return str(obj.customer_profile.total_spent)
        return '0.00'
    
    def get_last_order_date(self, obj):
        """Get last order date from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.last_order_date:
            return obj.customer_profile.last_order_date.isoformat()
        return None


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users - only shows first_name, last_name, email, and status"""
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'status']
        read_only_fields = ['id', 'first_name', 'last_name', 'email', 'status']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'

class ClientListSerializer(serializers.ModelSerializer):
    """Serializer for listing clients - includes customer fields"""
    status = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_contact_method = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'status', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date']
        read_only_fields = ['id', 'first_name', 'last_name', 'email', 'status', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'
    
    def get_created_by_name(self, obj):
        """Get the name of the user who created this user"""
        # Check if created_by exists on the model
        if hasattr(obj, 'created_by') and obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None
    
    def get_updated_by_name(self, obj):
        """Get the name of the user who last updated this user"""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None
    
    def get_phone_number(self, obj):
        """Get phone number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.phone_number
        return None
    
    def get_whatsapp_number(self, obj):
        """Get whatsapp number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.whatsapp_number
        return None
    
    def get_address(self, obj):
        """Get address from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.address
        return None
    
    def get_preferred_contact_method(self, obj):
        """Get preferred contact method from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.preferred_contact_method
        return None
    
    def get_notes(self, obj):
        """Get notes from customer profile - only if user is a client, show 'no note' if empty"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            notes = obj.customer_profile.notes
            return notes if notes else 'no note'
        return None
    
    def get_total_orders(self, obj):
        """Get total orders from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.total_orders
        return 0
    
    def get_total_spent(self, obj):
        """Get total spent from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return str(obj.customer_profile.total_spent)
        return '0.00'
    
    def get_last_order_date(self, obj):
        """Get last order date from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.last_order_date:
            return obj.customer_profile.last_order_date.isoformat()
        return None

# Custom exception classes for login errors
class InvalidCredentialsError(ValidationError):
    """Raised when credentials are invalid"""
    error_code = 'INVALID_CREDENTIALS'
    status_code = 401

class AccountInactiveError(ValidationError):
    """Raised when account is inactive"""
    error_code = 'ACCOUNT_INACTIVE'
    status_code = 401
    
    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = {
                'error_code': 'ACCOUNT_INACTIVE',
                'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                'status_code': 401
            }
        super().__init__(detail, code)

class MissingFieldsError(ValidationError):
    """Raised when required fields are missing"""
    error_code = 'MISSING_FIELDS'
    status_code = 400

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, write_only=True, allow_blank=False)
    
    def validate_username(self, value):
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Username and password are required',
                'status_code': 400
            })
        return value
    
    def validate_password(self, value):
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Username and password are required',
                'status_code': 400
            })
        return value
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Check if fields are present (double check)
        if not username or not password:
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Username and password are required',
                'status_code': 400
            })
        
        # First check if user exists and is inactive (before authentication)
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                raise AccountInactiveError({
                    'error_code': 'ACCOUNT_INACTIVE',
                    'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                    'status_code': 401
                })
        except User.DoesNotExist:
            pass  # User doesn't exist, will be caught by authenticate below
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is None:
            raise InvalidCredentialsError({
                'error_code': 'INVALID_CREDENTIALS',
                'message': 'Invalid username or password',
                'status_code': 401
            })
        
        # Double check if account is active (in case authenticate returned an inactive user)
        if not user.is_active:
            raise AccountInactiveError({
                'error_code': 'ACCOUNT_INACTIVE',
                'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                'status_code': 401
            })
        
        attrs['user'] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    Requires old password verification and new password.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "New password and confirm password do not match."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['user']
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        """Validate that new password is not the default password"""
        from django.conf import settings
        default_password = getattr(settings, 'DEFAULT_CUSTOMER_PASSWORD', 'ChangeMe123!')
        
        # Check if the new password matches the default password
        if value == default_password:
            raise serializers.ValidationError("You cannot use the default password. Please choose a different password.")
        
        return value


class UserCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by']

class ClientSelfUpdateSerializer(serializers.ModelSerializer):
    """Serializer for clients to update their own profile - includes customer fields"""
    # Customer fields
    phone_number = serializers.CharField(required=False, max_length=20, source='customer_profile.phone_number')
    whatsapp_number = serializers.CharField(required=False, max_length=20, source='customer_profile.whatsapp_number')
    address = serializers.CharField(required=False, source='customer_profile.address')
    preferred_contact_method = serializers.CharField(required=False, max_length=20, source='customer_profile.preferred_contact_method')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_username(self, value):
        """Check if username is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Check if email is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def update(self, instance, validated_data):
        """Update both User and Customer fields"""
        customer_data = {}
        
        # Separate customer and user fields - pop customer fields to prevent DRF issues
        customer_fields = ['phone_number', 'whatsapp_number', 'address', 'preferred_contact_method']
        
        # Also check for nested customer_profile dict (DRF might create this)
        if 'customer_profile' in validated_data:
            # DRF created a nested dict, extract it
            nested_data = validated_data.pop('customer_profile')
            if isinstance(nested_data, dict):
                customer_data.update(nested_data)
        
        # Pop individual customer fields
        for field in customer_fields:
            if field in validated_data:
                customer_data[field] = validated_data.pop(field)
        
        # Update user fields (remaining in validated_data)
        # Only update fields that exist on the User model
        user_fields_to_update = {}
        for field, value in validated_data.items():
            if field != 'customer_profile' and hasattr(instance, field):
                user_fields_to_update[field] = value
        
        # Update user fields
        for field, value in user_fields_to_update.items():
            setattr(instance, field, value)
        
        if user_fields_to_update:
            instance.updated_at = timezone.now()
            instance.updated_by = instance
            instance.save()
        
        # Update customer fields if customer data is provided
        if customer_data:
            # Get or create customer profile
            try:
                customer = instance.customer_profile
            except Customer.DoesNotExist:
                # Create customer if it doesn't exist
                from customers.models import Customer
                customer = Customer.objects.create(
                    user=instance,
                    phone_number='',
                    whatsapp_number='',
                    address='',
                    preferred_contact_method='phone',
                    notes='',
                    created_by=None,
                    updated_by=instance
                )
            
            # Update customer fields
            for field, value in customer_data.items():
                if hasattr(customer, field) and value is not None:
                    setattr(customer, field, value)
            customer.updated_by = instance
            customer.save()
        
        return instance

class AdminSelfUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admins to update their own profile - cannot change status or role"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_username(self, value):
        """Check if username is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Check if email is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value

class EmployeeSelfUpdateSerializer(serializers.ModelSerializer):
    """Serializer for employees to update their own profile - cannot change status or role"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_username(self, value):
        """Check if username is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Check if email is unique (excluding current user)"""
        user = self.context.get('user')
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value

class AdminUpdateEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for admins to update employees - can change is_active, is_staff, but NOT role, is_superuser, or username"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        extra_kwargs = {
            'username': {'required': False, 'read_only': True},  # Username cannot be edited by others
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
        }
    
    def validate_username(self, value):
        """Prevent editing other users' usernames"""
        # Username is read-only, so this should not be called, but add safety check
        raise serializers.ValidationError("Username cannot be changed by other users. Only the user themselves can change their username.")

class StaffUpdateClientSerializer(serializers.ModelSerializer):
    """Serializer for staff (employee, admin, superadmin) to update clients - can change is_active, is_staff, but NOT role or username"""
    # Customer fields
    phone_number = serializers.CharField(required=False, max_length=20, source='customer_profile.phone_number')
    whatsapp_number = serializers.CharField(required=False, max_length=20, source='customer_profile.whatsapp_number')
    address = serializers.CharField(required=False, source='customer_profile.address')
    preferred_contact_method = serializers.CharField(required=False, max_length=20, source='customer_profile.preferred_contact_method')
    notes = serializers.CharField(required=False, source='customer_profile.notes')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes']
        extra_kwargs = {
            'username': {'required': False, 'read_only': True},  # Username cannot be edited by others
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
        }
    
    def validate_username(self, value):
        """Prevent editing other users' usernames"""
        # Username is read-only, so this should not be called, but add safety check
        raise serializers.ValidationError("Username cannot be changed by other users. Only the user themselves can change their username.")
    
    def validate_email(self, value):
        """Check if email is unique (excluding the client being updated)"""
        # Get the instance (client being updated) from the serializer
        instance = getattr(self, 'instance', None)
        if instance:
            # Exclude the client being updated
            if User.objects.filter(email=value).exclude(id=instance.id).exists():
                raise serializers.ValidationError("Email already exists")
        else:
            # If no instance, check if email exists at all
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists")
        return value
    
    def update(self, instance, validated_data):
        """Update both User and Customer fields"""
        customer_data = {}
        
        # Separate customer and user fields - pop customer fields to prevent DRF issues
        customer_fields = ['phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes']
        
        # Also check for nested customer_profile dict (DRF might create this)
        if 'customer_profile' in validated_data:
            # DRF created a nested dict, extract it
            nested_data = validated_data.pop('customer_profile')
            if isinstance(nested_data, dict):
                customer_data.update(nested_data)
        
        # Pop individual customer fields
        for field in customer_fields:
            if field in validated_data:
                customer_data[field] = validated_data.pop(field)
        
        # Update user fields (remaining in validated_data)
        # Only update fields that exist on the User model
        user_fields_to_update = {}
        for field, value in validated_data.items():
            if field != 'customer_profile' and hasattr(instance, field):
                user_fields_to_update[field] = value
        
        # Update user fields
        for field, value in user_fields_to_update.items():
            setattr(instance, field, value)
        
        if user_fields_to_update:
            instance.save()
        
        # Update customer fields if customer data is provided
        if customer_data:
            # Get or create customer profile
            try:
                customer = instance.customer_profile
            except Customer.DoesNotExist:
                # Create customer if it doesn't exist
                customer = Customer.objects.create(
                    user=instance,
                    phone_number='',
                    whatsapp_number='',
                    address='',
                    preferred_contact_method='phone',
                    notes='',
                    created_by=self.context.get('user'),
                    updated_by=self.context.get('user')
                )
            
            # Update customer fields
            for field, value in customer_data.items():
                if hasattr(customer, field) and value is not None:
                    setattr(customer, field, value)
            customer.updated_by = self.context.get('user')
            customer.save()
        
        return instance

class SuperadminUpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for superadmin to update any user - full control including role promotion, but NOT username"""
    # Customer fields (only for clients)
    phone_number = serializers.CharField(required=False, max_length=20, source='customer_profile.phone_number', allow_null=True)
    whatsapp_number = serializers.CharField(required=False, max_length=20, source='customer_profile.whatsapp_number', allow_null=True)
    address = serializers.CharField(required=False, source='customer_profile.address', allow_null=True)
    preferred_contact_method = serializers.CharField(required=False, max_length=20, source='customer_profile.preferred_contact_method', allow_null=True)
    notes = serializers.CharField(required=False, source='customer_profile.notes', allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes']
        extra_kwargs = {
            'username': {'required': False, 'read_only': True},  # Username cannot be edited by others
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }
    
    def validate_username(self, value):
        """Prevent editing other users' usernames"""
        # Username is read-only, so this should not be called, but add safety check
        raise serializers.ValidationError("Username cannot be changed by other users. Only the user themselves can change their username.")
    
    def validate_role(self, value):
        """Validate role changes"""
        user = self.context.get('target_user')
        if user and user.role == 'superadmin' and value != 'superadmin':
            raise serializers.ValidationError("Cannot demote superadmin")
        return value
    
    def update(self, instance, validated_data):
        """Update both User and Customer fields (if client)"""
        customer_data = {}
        
        # Store original role to detect role changes
        original_role = instance.role
        was_staff = original_role in ['superadmin', 'admin', 'employee']
        
        # Separate customer and user fields - pop customer fields to prevent DRF issues
        customer_fields = ['phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes']
        
        # Also check for nested customer_profile dict (DRF might create this)
        if 'customer_profile' in validated_data:
            # DRF created a nested dict, extract it
            nested_data = validated_data.pop('customer_profile')
            if isinstance(nested_data, dict):
                customer_data.update(nested_data)
        
        # Pop individual customer fields
        for field in customer_fields:
            if field in validated_data:
                customer_data[field] = validated_data.pop(field)
        
        # Update user fields (remaining in validated_data)
        # Only update fields that exist on the User model
        user_fields_to_update = {}
        for field, value in validated_data.items():
            if field != 'customer_profile' and hasattr(instance, field):
                user_fields_to_update[field] = value
        
        # Check if role is being changed
        new_role = user_fields_to_update.get('role', original_role)
        role_changed = 'role' in user_fields_to_update and new_role != original_role
        
        # Automatically update is_staff and is_superuser based on role
        # IMPORTANT: Always override is_staff and is_superuser when role changes,
        # even if they were explicitly provided in the request
        if role_changed:
            # Remove any existing is_staff and is_superuser values to ensure our role-based values take precedence
            user_fields_to_update.pop('is_staff', None)
            user_fields_to_update.pop('is_superuser', None)
            
            if new_role == 'superadmin':
                # Force is_staff and is_superuser to True for superadmin
                user_fields_to_update['is_staff'] = True
                user_fields_to_update['is_superuser'] = True
            elif new_role in ['admin', 'employee']:
                # Force is_staff to True and is_superuser to False for admin/employee
                user_fields_to_update['is_staff'] = True
                user_fields_to_update['is_superuser'] = False
            elif new_role == 'client':
                # Force is_staff and is_superuser to False for client
                user_fields_to_update['is_staff'] = False
                user_fields_to_update['is_superuser'] = False
                
                # If changing from staff to client, check if customer profile exists
                if was_staff:
                    # Check if customer profile exists
                    has_customer_profile = False
                    try:
                        instance.customer_profile
                        has_customer_profile = True
                    except Customer.DoesNotExist:
                        has_customer_profile = False
                    
                    # If no customer profile exists, prevent conversion to client
                    if not has_customer_profile:
                        raise serializers.ValidationError({
                            'role': 'Cannot convert staff member to client. This user does not have customer details. Only users who were originally clients can be converted back to client role.'
                        })
        
        # Update user fields
        for field, value in user_fields_to_update.items():
            setattr(instance, field, value)
        
        if user_fields_to_update:
            # Set updated_by if user is in context
            if self.context.get('user'):
                instance.updated_by = self.context.get('user')
            instance.save()
        
        # Update customer fields only if user is a client
        if instance.role == 'client':
            # Get or create customer profile
            try:
                customer = instance.customer_profile
            except Customer.DoesNotExist:
                # Create customer if it doesn't exist (should have data from validation above)
                customer = Customer.objects.create(
                    user=instance,
                    phone_number=customer_data.get('phone_number', ''),
                    whatsapp_number=customer_data.get('whatsapp_number', ''),
                    address=customer_data.get('address', ''),
                    preferred_contact_method=customer_data.get('preferred_contact_method', 'phone'),
                    notes=customer_data.get('notes', ''),
                    created_by=self.context.get('user'),
                    updated_by=self.context.get('user')
                )
            
            # Update customer fields if customer data is provided
            if customer_data:
                for field, value in customer_data.items():
                    if hasattr(customer, field) and value is not None:
                        setattr(customer, field, value)
                customer.updated_by = self.context.get('user')
                customer.save()
        
        return instance

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for superadmin to get full user details - includes customer fields if client"""
    status = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    has_customer_profile = serializers.SerializerMethodField()
    # Customer fields
    phone_number = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_contact_method = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    customer_created_by_name = serializers.SerializerMethodField()
    customer_updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by_name', 'has_customer_profile', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by_name', 'status', 'has_customer_profile', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'
    
    def get_updated_by_name(self, obj):
        """Get the name of the user who last updated this user"""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None
    
    def get_has_customer_profile(self, obj):
        """Check if user has a customer profile"""
        return hasattr(obj, 'customer_profile')
    
    def get_customer_created_by_name(self, obj):
        """Get the name of the user who created the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.created_by:
            return f"{obj.customer_profile.created_by.first_name} {obj.customer_profile.created_by.last_name}".strip() or obj.customer_profile.created_by.username
        return None
    
    def get_customer_updated_by_name(self, obj):
        """Get the name of the user who last updated the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.updated_by:
            return f"{obj.customer_profile.updated_by.first_name} {obj.customer_profile.updated_by.last_name}".strip() or obj.customer_profile.updated_by.username
        return None
    
    def get_phone_number(self, obj):
        """Get phone number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.phone_number
        return None
    
    def get_whatsapp_number(self, obj):
        """Get whatsapp number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.whatsapp_number
        return None
    
    def get_address(self, obj):
        """Get address from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.address
        return None
    
    def get_preferred_contact_method(self, obj):
        """Get preferred contact method from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.preferred_contact_method
        return None
    
    def get_notes(self, obj):
        """Get notes from customer profile - only if user is a client, show 'no note' if empty"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            notes = obj.customer_profile.notes
            return notes if notes else 'no note'
        return None
    
    def get_total_orders(self, obj):
        """Get total orders from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.total_orders
        return 0
    
    def get_total_spent(self, obj):
        """Get total spent from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return str(obj.customer_profile.total_spent)
        return '0.00'
    
    def get_last_order_date(self, obj):
        """Get last order date from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.last_order_date:
            return obj.customer_profile.last_order_date.isoformat()
        return None

class staffGetUserByIdSerializer(serializers.ModelSerializer):
    """Serializer for staff (employee, admin, superadmin) to get user by id - returns user details with customer fields if client"""
    status = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    has_customer_profile = serializers.SerializerMethodField()
    # Customer fields
    phone_number = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    preferred_contact_method = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    customer_created_by_name = serializers.SerializerMethodField()
    customer_updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_active', 'is_staff', 'date_joined', 'updated_by_name', 'has_customer_profile', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
        read_only_fields = ['id', 'date_joined', 'status', 'updated_by_name', 'has_customer_profile', 'phone_number', 'whatsapp_number', 'address', 'preferred_contact_method', 'notes', 'total_orders', 'total_spent', 'last_order_date', 'customer_created_by_name', 'customer_updated_by_name']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'
    
    def get_updated_by_name(self, obj):
        """Get the name of the user who last updated this user"""
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip() or obj.updated_by.username
        return None
    
    def get_has_customer_profile(self, obj):
        """Check if user has a customer profile"""
        return hasattr(obj, 'customer_profile')
    
    def get_customer_created_by_name(self, obj):
        """Get the name of the user who created the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.created_by:
            return f"{obj.customer_profile.created_by.first_name} {obj.customer_profile.created_by.last_name}".strip() or obj.customer_profile.created_by.username
        return None
    
    def get_customer_updated_by_name(self, obj):
        """Get the name of the user who last updated the customer profile"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.updated_by:
            return f"{obj.customer_profile.updated_by.first_name} {obj.customer_profile.updated_by.last_name}".strip() or obj.customer_profile.updated_by.username
        return None
    
    def get_phone_number(self, obj):
        """Get phone number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.phone_number
        return None
    
    def get_whatsapp_number(self, obj):
        """Get whatsapp number from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.whatsapp_number
        return None
    
    def get_address(self, obj):
        """Get address from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.address
        return None
    
    def get_preferred_contact_method(self, obj):
        """Get preferred contact method from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.preferred_contact_method
        return None
    
    def get_notes(self, obj):
        """Get notes from customer profile - only if user is a client, show 'no note' if empty"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            notes = obj.customer_profile.notes
            return notes if notes else 'no note'
        return None
    
    def get_total_orders(self, obj):
        """Get total orders from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return obj.customer_profile.total_orders
        return 0
    
    def get_total_spent(self, obj):
        """Get total spent from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile'):
            return str(obj.customer_profile.total_spent)
        return '0.00'
    
    def get_last_order_date(self, obj):
        """Get last order date from customer profile - only if user is a client"""
        if obj.role == 'client' and hasattr(obj, 'customer_profile') and obj.customer_profile.last_order_date:
            return obj.customer_profile.last_order_date.isoformat()
        return None

