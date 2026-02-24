from rest_framework.response import Response


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
