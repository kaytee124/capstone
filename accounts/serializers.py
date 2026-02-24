from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by']

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users - only shows first_name, last_name, email, and status"""
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'status']
        read_only_fields = ['first_name', 'last_name', 'email', 'status']
    
    def get_status(self, obj):
        """Return 'active' or 'inactive' based on is_active field"""
        return 'active' if obj.is_active else 'inactive'

# Custom exception classes for login errors
class InvalidCredentialsError(ValidationError):
    """Raised when credentials are invalid"""
    error_code = 'INVALID_CREDENTIALS'
    status_code = 401

class AccountInactiveError(ValidationError):
    """Raised when account is inactive"""
    error_code = 'ACCOUNT_INACTIVE'
    status_code = 401

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
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is None:
            raise InvalidCredentialsError({
                'error_code': 'INVALID_CREDENTIALS',
                'message': 'Invalid username or password',
                'status_code': 401
            })
        
        # Check if account is active
        if not user.is_active:
            raise AccountInactiveError({
                'error_code': 'ACCOUNT_INACTIVE',
                'message': 'Your account has been deactivated',
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


class UserCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by']

class ClientSelfUpdateSerializer(serializers.ModelSerializer):
    """Serializer for clients to update their own profile - cannot change is_active"""
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
    """Serializer for admins to update employees - can change is_active, is_staff, but NOT role or is_superuser"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
        }

class StaffUpdateClientSerializer(serializers.ModelSerializer):
    """Serializer for staff (employee, admin, superadmin) to update clients - can change is_active, is_staff, but NOT role"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
        }

class SuperadminUpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for superadmin to update any user - full control including role promotion"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': False},
            'is_active': {'required': False},
            'is_staff': {'required': False},
            'is_superuser': {'required': False},
        }
    
    def validate_role(self, value):
        """Validate role changes"""
        user = self.context.get('target_user')
        if user and user.role == 'superadmin' and value != 'superadmin':
            raise serializers.ValidationError("Cannot demote superadmin")
        return value

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'updated_at', 'updated_by']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'updated_by']