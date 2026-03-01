from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Customer
from accounts.models import User
import re

# Custom exception classes for customer registration errors
class UsernameExistsError(ValidationError):
    """Raised when username already exists"""
    error_code = 'USERNAME_EXISTS'
    status_code = 409

class EmailExistsError(ValidationError):
    """Raised when email already exists"""
    error_code = 'EMAIL_EXISTS'
    status_code = 409

class PhoneExistsError(ValidationError):
    """Raised when phone number already exists"""
    error_code = 'PHONE_EXISTS'
    status_code = 409

class WhatsAppExistsError(ValidationError):
    """Raised when WhatsApp number already exists"""
    error_code = 'WHATSAPP_EXISTS'
    status_code = 409

class InvalidPasswordError(ValidationError):
    """Raised when password is invalid"""
    error_code = 'INVALID_PASSWORD'
    status_code = 422

class InvalidEmailError(ValidationError):
    """Raised when email format is invalid"""
    error_code = 'INVALID_EMAIL'
    status_code = 422

class MissingFieldsError(ValidationError):
    """Raised when required fields are missing"""
    error_code = 'MISSING_FIELDS'
    status_code = 400

class CustomerRegistrationSerializer(serializers.Serializer):
    """Serializer for customer self-registration"""
    # User fields
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    
    # Customer fields
    phone_number = serializers.CharField(required=True, max_length=20)
    whatsapp_number = serializers.CharField(required=True, max_length=20)
    address = serializers.CharField(required=True)
    preferred_contact_method = serializers.ChoiceField(
        choices=[('phone', 'Phone'), ('whatsapp', 'Whatsapp')], 
        required=True
    )
    
    def validate_username(self, value):
        """Check if username is provided and not already taken"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if User.objects.filter(username=value).exists():
            raise UsernameExistsError({
                'error_code': 'USERNAME_EXISTS',
                'message': 'Username already taken',
                'status_code': 409
            })
        return value
    
    def validate_email(self, value):
        """Check if email is valid and not already registered"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise InvalidEmailError({
                'error_code': 'INVALID_EMAIL',
                'message': 'Invalid email format',
                'status_code': 422
            })
        
        if User.objects.filter(email=value).exists():
            raise EmailExistsError({
                'error_code': 'EMAIL_EXISTS',
                'message': 'Email already registered',
                'status_code': 409
            })
        return value
    
    def validate_password(self, value):
        """Check if password meets requirements"""
        if not value:
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if len(value) < 8:
            raise InvalidPasswordError({
                'error_code': 'INVALID_PASSWORD',
                'message': 'Password must be at least 8 characters',
                'status_code': 422
            })
        return value
    
    def validate_phone_number(self, value):
        """Check if phone number is provided and not already registered"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if Customer.objects.filter(phone_number=value).exists():
            raise PhoneExistsError({
                'error_code': 'PHONE_EXISTS',
                'message': 'Phone number already registered',
                'status_code': 409
            })
        return value
    
    def validate_whatsapp_number(self, value):
        """Check if whatsapp number is provided and not already registered"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if Customer.objects.filter(whatsapp_number=value).exists():
            raise WhatsAppExistsError({
                'error_code': 'WHATSAPP_EXISTS',
                'message': 'WhatsApp number already registered',
                'status_code': 409
            })
        return value
    
    def validate_first_name(self, value):
        """Check if first name is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def validate_last_name(self, value):
        """Check if last name is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def validate_address(self, value):
        """Check if address is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def create(self, validated_data):
        """Create User and Customer in a transaction"""
        from django.db import transaction
        from django.utils import timezone
        
        # Get current timestamp
        now = timezone.now()
        
        # Extract user and customer data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'password': validated_data['password'],
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'role': 'client',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
        
        customer_data = {
            'phone_number': validated_data['phone_number'],
            'whatsapp_number': validated_data['whatsapp_number'],
            'address': validated_data['address'],
            'preferred_contact_method': validated_data['preferred_contact_method'],
            'notes': '',  # Empty notes for self-registration
            'created_by': None,  # No created_by when customer registers themselves
            'updated_by': None,  # No updated_by when customer registers themselves
        }
        
        with transaction.atomic():
            # Create User
            user = User.objects.create_user(**user_data)
            
            # Explicitly set date_joined and updated_at for User
            user.date_joined = now
            user.updated_at = now
            user.save()
            
            # Create Customer linked to the User
            customer = Customer.objects.create(
                user=user,
                **customer_data
            )
            
            # Explicitly set created_at and updated_at for Customer
            customer.created_at = now
            customer.updated_at = now
            customer.save()
        
        return customer

class AdminCustomerCreationSerializer(serializers.Serializer):
    """Serializer for admin/employee creating customers with user creation"""
    # User fields
    username = serializers.CharField(required=True, max_length=150)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    
    # Customer fields
    phone_number = serializers.CharField(required=True, max_length=20)
    whatsapp_number = serializers.CharField(required=True, max_length=20)
    address = serializers.CharField(required=True)
    preferred_contact_method = serializers.ChoiceField(
        choices=[('phone', 'Phone'), ('whatsapp', 'Whatsapp')], 
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate_username(self, value):
        """Check if username is provided and not already exists"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if User.objects.filter(username=value).exists():
            raise UsernameExistsError({
                'error_code': 'USERNAME_EXISTS',
                'message': 'Username already taken',
                'status_code': 409
            })
        return value
    
    def validate_email(self, value):
        """Check if email is provided, valid, and not already exists"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise InvalidEmailError({
                'error_code': 'INVALID_EMAIL',
                'message': 'Invalid email format',
                'status_code': 422
            })
        
        if User.objects.filter(email=value).exists():
            raise EmailExistsError({
                'error_code': 'EMAIL_EXISTS',
                'message': 'Email already registered',
                'status_code': 409
            })
        return value
    
    def validate_phone_number(self, value):
        """Check if phone number is provided and not already exists"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if Customer.objects.filter(phone_number=value).exists():
            raise PhoneExistsError({
                'error_code': 'PHONE_EXISTS',
                'message': 'Phone number already registered',
                'status_code': 409
            })
        return value
    
    def validate_first_name(self, value):
        """Check if first name is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def validate_last_name(self, value):
        """Check if last name is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def validate_address(self, value):
        """Check if address is provided"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        return value
    
    def validate_whatsapp_number(self, value):
        """Check if whatsapp number is provided and not already registered"""
        if not value or value.strip() == '':
            raise MissingFieldsError({
                'error_code': 'MISSING_FIELDS',
                'message': 'Required fields missing',
                'status_code': 400
            })
        
        if Customer.objects.filter(whatsapp_number=value).exists():
            raise WhatsAppExistsError({
                'error_code': 'WHATSAPP_EXISTS',
                'message': 'WhatsApp number already registered',
                'status_code': 409
            })
        return value
    
    def create(self, validated_data):
        """Create User and Customer with default password"""
        from django.db import transaction
        from django.utils import timezone
        from django.conf import settings
        
        # Get current timestamp
        now = timezone.now()
        
        # Get the admin/employee creating the customer (from context)
        creator = self.context.get('user')
        
        # Extract user and customer data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'password': settings.DEFAULT_CUSTOMER_PASSWORD,  # Default password
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'role': 'client',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
        
        customer_data = {
            'phone_number': validated_data['phone_number'],
            'whatsapp_number': validated_data['whatsapp_number'],
            'address': validated_data['address'],
            'preferred_contact_method': validated_data['preferred_contact_method'],
            'notes': validated_data.get('notes', ''),
            'created_by': creator,  # Admin/employee who created the customer
            'updated_by': creator,
        }
        
        with transaction.atomic():
            # Create User with default password
            user = User.objects.create_user(**user_data)
            
            # Explicitly set date_joined and updated_at for User
            user.date_joined = now
            user.updated_at = now
            user.updated_by = creator
            user.save()
            
            # Create Customer linked to the User
            customer = Customer.objects.create(
                user=user,
                **customer_data
            )
            
            # Explicitly set created_at and updated_at for Customer
            customer.created_at = now
            customer.updated_at = now
            customer.save()
        
        return customer

