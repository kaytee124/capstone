"""
Custom exception handler for DRF to format authentication errors
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from django.shortcuts import redirect
from django.urls import reverse
from accounts.serializers import AccountInactiveError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats authentication errors
    with custom error codes and messages.
    For HTML requests, redirects to login with error messages.
    """
    request = context.get('request')
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Check if this is an HTML request (not API/JSON)
        is_html_request = not request.headers.get('Accept', '').startswith('application/json')
        
        # Handle account inactive error
        if isinstance(exc, AccountInactiveError):
            if is_html_request:
                intended_url = request.get_full_path()
                error_message = exc.detail.get('message', 'Your account has been deactivated. Please contact the administrator for assistance.') if hasattr(exc, 'detail') else 'Your account has been deactivated. Please contact the administrator for assistance.'
                login_url = f"{reverse('user_login')}?error=ACCOUNT_INACTIVE&message={error_message}"
                return redirect(login_url)
            
            error_detail = exc.detail if hasattr(exc, 'detail') else {
                'error_code': 'ACCOUNT_INACTIVE',
                'message': 'Your account has been deactivated. Please contact the administrator for assistance.',
                'status_code': 401
            }
            response.data = error_detail
            response.status_code = status.HTTP_401_UNAUTHORIZED
        
        # Handle authentication errors
        elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            if is_html_request:
                # Prevent redirect loop - don't redirect if already on login page
                current_path = request.get_full_path()
                login_path = reverse('user_login')
                
                # Check if we're already on the login page or if next points to login
                if login_path in current_path or (request.GET.get('next') and login_path in request.GET.get('next', '')):
                    # Already on login page, just return the response without redirect
                    response.data = {
                        'error_code': 'NO_TOKEN',
                        'message': 'Authentication required. Please log in to continue.',
                        'status_code': 401
                    }
                    response.status_code = status.HTTP_401_UNAUTHORIZED
                    return response
                
                # Store the intended URL for redirect after login
                intended_url = request.get_full_path()
                login_url = f"{login_path}?next={intended_url}&error=NO_TOKEN&message=Authentication required. Please log in to continue."
                return redirect(login_url)
            
            response.data = {
                'error_code': 'NO_TOKEN',
                'message': 'Authentication credentials not provided',
                'status_code': 401
            }
            response.status_code = status.HTTP_401_UNAUTHORIZED
            
        elif isinstance(exc, (InvalidToken, TokenError)):
            if is_html_request:
                # Prevent redirect loop - don't redirect if already on login page
                current_path = request.get_full_path()
                login_path = reverse('user_login')
                
                if login_path in current_path or (request.GET.get('next') and login_path in request.GET.get('next', '')):
                    response.data = {
                        'error_code': 'INVALID_TOKEN',
                        'message': 'Your session has expired. Please log in again.',
                        'status_code': 401
                    }
                    response.status_code = status.HTTP_401_UNAUTHORIZED
                    return response
                
                intended_url = request.get_full_path()
                login_url = f"{login_path}?next={intended_url}&error=INVALID_TOKEN&message=Your session has expired. Please log in again."
                return redirect(login_url)
            
            response.data = {
                'error_code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token',
                'status_code': 401
            }
            response.status_code = status.HTTP_401_UNAUTHORIZED
            
        elif isinstance(exc, PermissionDenied):
            if is_html_request:
                # For permission denied, redirect to profile or last accessible page
                # Try to get the user's profile URL or default to profile
                try:
                    if request.user and request.user.is_authenticated:
                        # User is authenticated but doesn't have permission
                        # Redirect to their profile with error message
                        profile_url = f"{reverse('user_profile')}?error=PERMISSION_DENIED&message=You don't have permission to access this page."
                        return redirect(profile_url)
                except:
                    pass
                
                # If user is not authenticated, redirect to login
                intended_url = request.get_full_path()
                login_url = f"{reverse('user_login')}?next={intended_url}&error=PERMISSION_DENIED&message=You don't have permission to access this page. Please log in with an account that has the required permissions."
                return redirect(login_url)
            
            response.data = {
                'error_code': 'PERMISSION_DENIED',
                'message': 'You do not have permission to perform this action',
                'status_code': 403
            }
            response.status_code = status.HTTP_403_FORBIDDEN
    
    return response
