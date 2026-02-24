// API Utility - Handles token management and auto-refresh
// Include this file in all pages that make API calls

// Token management functions
const TokenManager = {
    // Get access token from localStorage
    getAccessToken: function() {
        return localStorage.getItem('access_token');
    },
    
    // Get refresh token from localStorage
    getRefreshToken: function() {
        return localStorage.getItem('refresh_token');
    },
    
    // Set access token
    setAccessToken: function(token) {
        localStorage.setItem('access_token', token);
    },
    
    // Set refresh token
    setRefreshToken: function(token) {
        localStorage.setItem('refresh_token', token);
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
    
    // Clear all tokens
    clearTokens: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
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
    
    // Process response for token updates (only for API calls with JSON responses)
    if (typeof url === 'string' && url.startsWith('/api/') && response.headers.get('content-type')?.includes('application/json')) {
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
    
    return response;
};
