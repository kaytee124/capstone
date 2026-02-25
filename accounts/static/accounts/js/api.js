// API Utility - Handles token management and auto-refresh
// Include this file in all pages that make API calls

// Token management functions
const TokenManager = {
    // Get access token from localStorage (with cookie fallback)
    getAccessToken: function() {
        let token = localStorage.getItem('access_token');
        if (!token) {
            // Fallback to cookie
            token = this.getCookie('access_token');
            if (token) {
                localStorage.setItem('access_token', token);
            }
        }
        return token;
    },

    // Get refresh token from localStorage (with cookie fallback)
    getRefreshToken: function() {
        let token = localStorage.getItem('refresh_token');
        if (!token) {
            // Fallback to cookie
            token = this.getCookie('refresh_token');
            if (token) {
                localStorage.setItem('refresh_token', token);
            }
        }
        return token;
    },

    // Set access token (both localStorage and cookie)
    setAccessToken: function(token) {
        localStorage.setItem('access_token', token);
        this.setCookie('access_token', token, 3600); // 1 hour
    },

    // Set refresh token (both localStorage and cookie)
    setRefreshToken: function(token) {
        localStorage.setItem('refresh_token', token);
        this.setCookie('refresh_token', token, 86400); // 1 day
    },
    
    // Helper to get cookie
    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    
    // Helper to set cookie
    setCookie: function(name, value, maxAge) {
        document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; SameSite=Lax`;
    },
    
    // Update tokens from response
    updateTokensFromResponse: function(responseData) {
        if (responseData.token_refreshed && responseData.new_access_token) {
            this.setAccessToken(responseData.new_access_token);
            
            if (responseData.new_refresh_token) {
                this.setRefreshToken(responseData.new_refresh_token);
            }
            
            console.log('Tokens automatically refreshed and updated in localStorage');
            return true;
        }
        return false;
    },
    
    // Clear all tokens (both localStorage and cookies)
    clearTokens: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        // Clear cookies
        this.setCookie('access_token', '', 0);
        this.setCookie('refresh_token', '', 0);
    }
};

// Enhanced fetch function that automatically handles tokens
async function apiFetch(url, options = {}) {
    // Get tokens
    const accessToken = TokenManager.getAccessToken();
    const refreshToken = TokenManager.getRefreshToken();
    
    // Prepare headers
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // Add access token to Authorization header if available
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    // Add refresh token to custom header for auto-refresh
    if (refreshToken) {
        headers['X-Refresh-Token'] = refreshToken;
    }
    
    // Add CSRF token if available
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    // Merge headers with options
    const fetchOptions = {
        ...options,
        headers: headers
    };
    
    try {
        const response = await fetch(url, fetchOptions);
        const data = await response.json();
        
        // Check if response contains new tokens (from auto-refresh)
        if (response.ok && data) {
            TokenManager.updateTokensFromResponse(data);
        }
        
        // Return response with data
        return {
            ...response,
            data: data
        };
    } catch (error) {
        console.error('API fetch error:', error);
        throw error;
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Global fetch interceptor to automatically handle tokens
// This intercepts all fetch calls to:
// 1. Automatically add tokens to headers
// 2. Automatically update tokens from responses
const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    // Only modify API calls
    if (typeof url === 'string' && url.startsWith('/api/')) {
        const accessToken = TokenManager.getAccessToken();
        const refreshToken = TokenManager.getRefreshToken();
        
        // Prepare headers
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };
        
        // Add access token if available and not already set
        if (accessToken && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }
        
        // Add refresh token for auto-refresh (if not already in headers)
        if (refreshToken && !headers['X-Refresh-Token']) {
            headers['X-Refresh-Token'] = refreshToken;
        }
        
        // Add CSRF token if available
        const csrfToken = getCookie('csrftoken');
        if (csrfToken && !headers['X-CSRFToken']) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        options.headers = headers;
    }
    
           // Call original fetch
           const response = await originalFetch(url, options);

           // Handle authentication and permission errors
           if (typeof url === 'string' && url.startsWith('/api/')) {
               // Handle 401 Unauthorized (authentication required)
               if (response.status === 401) {
                   // Clear tokens
                   TokenManager.clearTokens();
                   
                   // Get error message from response if available
                   let errorMessage = 'Authentication required. Please log in to continue.';
                   try {
                       const clonedResponse = response.clone();
                       const data = await clonedResponse.json();
                       if (data.message) {
                           errorMessage = data.message;
                       }
                   } catch (e) {
                       // Ignore if can't parse JSON
                   }
                   
                   // Redirect to login with current URL as next parameter
                   const currentUrl = window.location.pathname + window.location.search;
                   const loginUrl = `/api/accounts/login/?next=${encodeURIComponent(currentUrl)}&error=NO_TOKEN&message=${encodeURIComponent(errorMessage)}`;
                   window.location.href = loginUrl;
                   return response; // Return response but user will be redirected
               }
               
               // Handle 403 Forbidden (permission denied)
               if (response.status === 403) {
                   let errorMessage = 'You do not have permission to access this resource.';
                   try {
                       const clonedResponse = response.clone();
                       const data = await clonedResponse.json();
                       if (data.message) {
                           errorMessage = data.message;
                       }
                   } catch (e) {
                       // Ignore if can't parse JSON
                   }
                   
                   // Check if user is authenticated
                   const userData = localStorage.getItem('user');
                   if (userData) {
                       // User is authenticated but lacks permission - redirect to profile
                       const profileUrl = `/api/accounts/user/profile/?error=PERMISSION_DENIED&message=${encodeURIComponent(errorMessage)}`;
                       window.location.href = profileUrl;
                   } else {
                       // User is not authenticated - redirect to login
                       const currentUrl = window.location.pathname + window.location.search;
                       const loginUrl = `/api/accounts/login/?next=${encodeURIComponent(currentUrl)}&error=PERMISSION_DENIED&message=${encodeURIComponent(errorMessage)}`;
                       window.location.href = loginUrl;
                   }
                   return response;
               }
               
               // Process response for token updates (only for API calls with JSON responses)
               if (response.headers.get('content-type')?.includes('application/json')) {
                   const clonedResponse = response.clone();

                   try {
                       const data = await clonedResponse.json();

                       // Check if response contains new tokens (from auto-refresh)
                       if (data && data.token_refreshed && data.new_access_token) {
                           TokenManager.setAccessToken(data.new_access_token);

                           if (data.new_refresh_token) {
                               TokenManager.setRefreshToken(data.new_refresh_token);
                           }

                           console.log('✅ Tokens automatically refreshed and updated in localStorage');
                       }
                   } catch (e) {
                       // Not JSON or can't parse, ignore
                   }
               }
           }

           return response;
};
