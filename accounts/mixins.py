from rest_framework.response import Response
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class AutoRefreshTokenMixin:
    """
    Mixin to automatically add refreshed tokens to response.
    Use this mixin in views that need auto-refresh functionality.
    """
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override finalize_response to add new tokens to response if auto-refresh occurred.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Check if new tokens were generated during authentication
        if hasattr(request, '_new_access_token'):
            # Add new tokens to response data
            if isinstance(response.data, dict):
                response.data['new_access_token'] = request._new_access_token
                
                # Add new refresh token if rotation occurred
                if hasattr(request, '_new_refresh_token') and request._new_refresh_token:
                    response.data['new_refresh_token'] = request._new_refresh_token
                    response.data['token_rotated'] = True
                else:
                    response.data['token_rotated'] = False
                
                response.data['token_refreshed'] = True
        
        return response


class RequirePasswordChangeMixin:
    """
    Mixin to check if user needs to change password before accessing views.
    Redirects to password change page if user is using default password.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user needs to change password before processing request.
        """
        # Only check for authenticated users
        if request.user and request.user.is_authenticated:
            # Check if user is using default password
            if request.user.check_password(settings.DEFAULT_CUSTOMER_PASSWORD):
                # Allow access to change password page and logout
                if request.path not in ['/api/accounts/change-password/', '/api/accounts/logout/']:
                    # Check if this is an HTML request
                    if not request.headers.get('Accept', '').startswith('application/json'):
                        # Redirect to password change page
                        return redirect(reverse('change_password') + '?message=You must change your default password before accessing other pages.')
                    else:
                        # For API requests, return error response
                        from rest_framework.response import Response
                        from rest_framework import status
                        return Response({
                            'error_code': 'PASSWORD_CHANGE_REQUIRED',
                            'message': 'You must change your default password before accessing this resource',
                            'status_code': 403
                        }, status=status.HTTP_403_FORBIDDEN)
        
        return super().dispatch(request, *args, **kwargs)
