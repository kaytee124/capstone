from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import exceptions
import logging

logger = logging.getLogger(__name__)


class AutoRefreshJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that automatically refreshes expired tokens
    if a refresh token is provided in the request.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and auto-refresh token if expired.
        Also checks cookies for tokens (for browser navigation).
        """
        # Check for token in Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        # If no Authorization header, check cookies (for browser navigation)
        if not auth_header or not auth_header.startswith('Bearer '):
            access_token = request.COOKIES.get('access_token')
            if access_token:
                # Set the Authorization header from cookie
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        
        # First, try normal authentication
        try:
            return super().authenticate(request)
        except InvalidToken as e:
            # Token is invalid or expired, try to refresh it
            return self._try_auto_refresh(request, e)
        except Exception as e:
            # Other authentication errors
            raise
    
    def _try_auto_refresh(self, request, original_error):
        """
        Try to automatically refresh the token if refresh token is available.
        """
        # Check for refresh token in custom header, request data, or cookies
        refresh_token = (
            request.META.get('HTTP_X_REFRESH_TOKEN') or  # Custom header: X-Refresh-Token
            request.data.get('refresh_token') or  # Request body
            request.GET.get('refresh_token') or  # Query param (less secure, but available)
            request.COOKIES.get('refresh_token')  # Cookie (for browser navigation)
        )
        
        if not refresh_token:
            # No refresh token available, raise original error
            raise original_error
        
        try:
            # Try to refresh the token
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            # Get user from the refresh token
            from rest_framework_simplejwt.state import token_backend
            validated_token = token_backend.decode(refresh_token, verify=True)
            user_id = validated_token.get('user_id')
            
            if user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    
                    # Store new tokens in request for response headers
                    request._new_access_token = str(new_access_token)
                    
                    # Handle token rotation - get new refresh token if rotation is enabled
                    from django.conf import settings
                    if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                        try:
                            refresh.blacklist()  # Blacklist old refresh token
                        except Exception:
                            pass  # Blacklist might not be configured
                        new_refresh = RefreshToken.for_user(user)
                        request._new_refresh_token = str(new_refresh)
                    else:
                        request._new_refresh_token = None
                    
                    # Return authenticated user
                    return (user, None)  # Return tuple (user, token)
                except User.DoesNotExist:
                    raise InvalidToken('User not found')
            else:
                raise InvalidToken('Invalid token payload')
                
        except TokenError as e:
            # Refresh token is also invalid/expired
            logger.warning(f'Auto-refresh failed: {str(e)}')
            raise original_error
        except Exception as e:
            # Other errors during refresh
            logger.error(f'Auto-refresh error: {str(e)}', exc_info=True)
            raise original_error
