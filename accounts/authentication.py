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
            # For auto-refresh, we don't want to rotate tokens (which would blacklist the old one)
            # Instead, we'll manually refresh without rotation
            # This allows the refresh token to be reused until it expires
            refresh = RefreshToken(refresh_token)
            
            # Check if token is blacklisted
            try:
                refresh.check_blacklist()
            except Exception:
                # Token is blacklisted, can't use it
                raise InvalidToken('Token is blacklisted')
            
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
                    
                    # Store new access token in request for response headers
                    # Don't rotate refresh token on auto-refresh - keep using the same one
                    request._new_access_token = str(new_access_token)
                    request._new_refresh_token = None  # No rotation on auto-refresh
                    
                    # Return authenticated user
                    return (user, None)  # Return tuple (user, token)
                except User.DoesNotExist:
                    raise InvalidToken('User not found')
            else:
                raise InvalidToken('Invalid token payload')
            
            if serializer.is_valid():
                # Serializer handles token rotation and blacklisting automatically
                validated_data = serializer.validated_data
                new_access_token = validated_data.get('access')
                new_refresh_token = validated_data.get('refresh')  # Will be None if rotation disabled
                
                # Decode the new access token to get user_id
                from rest_framework_simplejwt.state import token_backend
                try:
                    # Decode the new access token to get user info
                    validated_token = token_backend.decode(new_access_token, verify=True)
                    user_id = validated_token.get('user_id')
                    
                    if user_id:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        try:
                            user = User.objects.get(id=user_id)
                            
                            # Store new tokens in request for response headers
                            request._new_access_token = new_access_token
                            # For auto-refresh, don't rotate refresh token to avoid blacklisting issues
                            # Only rotate on explicit refresh endpoint calls
                            request._new_refresh_token = None  # Don't rotate on auto-refresh
                            
                            # Return authenticated user
                            return (user, None)  # Return tuple (user, token)
                        except User.DoesNotExist:
                            raise InvalidToken('User not found')
                    else:
                        raise InvalidToken('Invalid token payload')
                except Exception as decode_error:
                    logger.error(f'Failed to decode new access token: {str(decode_error)}', exc_info=True)
                    raise InvalidToken('Failed to decode tokens')
            else:
                # Serializer validation failed
                raise InvalidToken('Invalid refresh token')
                
        except TokenError as e:
            # Refresh token is also invalid/expired
            logger.warning(f'Auto-refresh failed: {str(e)}')
            raise original_error
        except Exception as e:
            # Other errors during refresh
            logger.error(f'Auto-refresh error: {str(e)}', exc_info=True)
            raise original_error
