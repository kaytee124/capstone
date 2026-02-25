from rest_framework import serializers
from django.db import IntegrityError
from .models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'unit', 'category', 'estimated_days', 'is_active']
        read_only_fields = ['id']
    
    def validate_name(self, value):
        """Validate name is provided and not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError('Name is required')
        return value.strip()
    
    def validate_price(self, value):
        """Validate price is provided and greater than 0"""
        if value is None:
            raise serializers.ValidationError('Price is required')
        if value <= 0:
            raise serializers.ValidationError({
                'error_code': 'INVALID_PRICE',
                'message': 'Price must be greater than 0',
                'status_code': 422
            })
        return value
    
    def validate(self, attrs):
        """Validate required fields and check for duplicate names"""
        # For creation, name and price are required
        if not self.instance:
            if 'name' not in attrs or not attrs.get('name'):
                raise serializers.ValidationError({
                    'error_code': 'MISSING_FIELDS',
                    'message': 'Name and price are required',
                    'status_code': 400
                })
            
            if 'price' not in attrs or attrs.get('price') is None:
                raise serializers.ValidationError({
                    'error_code': 'MISSING_FIELDS',
                    'message': 'Name and price are required',
                    'status_code': 400
                })
        else:
            # For updates, if name or price is being updated, validate them
            # If name is being updated, it must not be empty
            if 'name' in attrs and (not attrs.get('name') or not attrs.get('name').strip()):
                raise serializers.ValidationError({
                    'error_code': 'MISSING_FIELDS',
                    'message': 'Name and price are required',
                    'status_code': 400
                })
            
            # If price is being updated, it must be valid
            if 'price' in attrs and attrs.get('price') is None:
                raise serializers.ValidationError({
                    'error_code': 'MISSING_FIELDS',
                    'message': 'Name and price are required',
                    'status_code': 400
                })
        
        # Check for duplicate service name (case-insensitive)
        # Only check if name is being updated
        if 'name' in attrs:
            name = attrs.get('name', '').strip()
            if name:
                existing_service = Service.objects.filter(name__iexact=name).first()
                # If updating, exclude current instance
                if self.instance:
                    if existing_service and existing_service.id != self.instance.id:
                        raise serializers.ValidationError({
                            'error_code': 'SERVICE_EXISTS',
                            'message': 'Service with this name already exists',
                            'status_code': 409
                        })
                # If creating, check if service exists
                elif existing_service:
                    raise serializers.ValidationError({
                        'error_code': 'SERVICE_EXISTS',
                        'message': 'Service with this name already exists',
                        'status_code': 409
                    })
        
        return attrs
    
    def create(self, validated_data):
        """Create service with created_by from context"""
        user = self.context.get('user')
        
        # Check for duplicate name one more time (race condition protection)
        name = validated_data.get('name', '').strip()
        if Service.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError({
                'error_code': 'SERVICE_EXISTS',
                'message': 'Service with this name already exists',
                'status_code': 409
            })
        
        # Only set created_by, not updated_by or updated_at
        # created_at and updated_at are auto fields, so they'll be set automatically
        try:
            service = Service.objects.create(
                created_by=user,
                **validated_data
            )
            return service
        except IntegrityError:
            # Handle database-level duplicate constraint
            raise serializers.ValidationError({
                'error_code': 'SERVICE_EXISTS',
                'message': 'Service with this name already exists',
                'status_code': 409
            })
    
    def update(self, instance, validated_data):
        """Update service with updated_by from context"""
        user = self.context.get('user')
        
        # Check for duplicate name one more time (race condition protection)
        if 'name' in validated_data:
            name = validated_data.get('name', '').strip()
            existing_service = Service.objects.filter(name__iexact=name).exclude(id=instance.id).first()
            if existing_service:
                raise serializers.ValidationError({
                    'error_code': 'SERVICE_EXISTS',
                    'message': 'Service with this name already exists',
                    'status_code': 409
                })
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Set updated_by
        instance.updated_by = user
        instance.save()
        
        return instance