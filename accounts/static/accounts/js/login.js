// Login Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const passwordToggle = document.getElementById('passwordToggle');
    const alertContainer = document.getElementById('alertContainer');
    const submitBtn = document.getElementById('submitBtn');
    
    // Show error message if present in URL
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const errorMessage = urlParams.get('message');
    
    if (error && errorMessage) {
        // Show the error alert if it exists in the template
        const existingAlert = alertContainer.querySelector('.alert');
        if (existingAlert) {
            alertContainer.classList.remove('hidden');
        } else {
            showAlert(errorMessage, error.toLowerCase().includes('permission') ? 'error' : 'error');
        }
    }

    // Password toggle functionality
    if (passwordToggle) {
        passwordToggle.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            const icon = passwordToggle.querySelector('svg');
            if (type === 'password') {
                icon.innerHTML = `
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                `;
            } else {
                icon.innerHTML = `
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                `;
            }
        });
    }

    // Form validation
    function validateForm() {
        let isValid = true;
        
        // Clear previous errors
        clearErrors();
        
        // Validate username
        if (!usernameInput.value.trim()) {
            showFieldError(usernameInput, 'Username is required');
            isValid = false;
        }
        
        // Validate password
        if (!passwordInput.value) {
            showFieldError(passwordInput, 'Password is required');
            isValid = false;
        } else if (passwordInput.value.length < 6) {
            showFieldError(passwordInput, 'Password must be at least 6 characters');
            isValid = false;
        }
        
        return isValid;
    }

    // Show field error
    function showFieldError(input, message) {
        input.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        input.parentElement.appendChild(errorDiv);
    }

    // Clear errors
    function clearErrors() {
        document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
        document.querySelectorAll('.error-message').forEach(el => el.remove());
    }

    // Show alert
    function showAlert(message, type = 'error') {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
                <span>${message}</span>
            </div>
        `;
        alertContainer.classList.remove('hidden');
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                alertContainer.classList.add('hidden');
            }, 5000);
        }
    }

    // Hide alert
    function hideAlert() {
        alertContainer.classList.add('hidden');
    }

    // Form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!validateForm()) {
                return;
            }
            
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Logging in...';
            
            try {
                const response = await fetch('/api/accounts/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        username: usernameInput.value.trim(),
                        password: passwordInput.value
                    })
                });
                
                // Check if response is JSON
                const contentType = response.headers.get('content-type');
                let data;
                
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    // Response is not JSON (might be HTML redirect)
                    const text = await response.text();
                    console.error('Non-JSON response:', text.substring(0, 200));
                    
                    // If it's a redirect or HTML, show appropriate error
                    if (response.redirected || response.status === 302 || response.status === 301) {
                        showAlert('Session expired. Please refresh the page and try again.', 'error');
                    } else {
                        showAlert('Invalid response from server. Please try again.', 'error');
                    }
                    
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                    return;
                }
                
                if (response.ok) {
                    // Store tokens - use TokenManager if available (from api.js), otherwise use localStorage directly
                    if (typeof TokenManager !== 'undefined') {
                        TokenManager.setAccessToken(data.access);
                        TokenManager.setRefreshToken(data.refresh);
                    } else {
                        localStorage.setItem('access_token', data.access);
                        localStorage.setItem('refresh_token', data.refresh);
                    }
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Check for auto-refreshed tokens (shouldn't happen on login, but just in case)
                    if (data.token_refreshed && data.new_access_token) {
                        if (typeof TokenManager !== 'undefined') {
                            TokenManager.setAccessToken(data.new_access_token);
                            if (data.new_refresh_token) {
                                TokenManager.setRefreshToken(data.new_refresh_token);
                            }
                        } else {
                            localStorage.setItem('access_token', data.new_access_token);
                            if (data.new_refresh_token) {
                                localStorage.setItem('refresh_token', data.new_refresh_token);
                            }
                        }
                    }
                    
                    // Check if password change is required
                    if (data.requires_password_change) {
                        showAlert('Please change your default password before continuing.', 'error');
                        // Store flag in localStorage to prevent navigation
                        localStorage.setItem('requires_password_change', 'true');
                        // Redirect to change password page
                        setTimeout(() => {
                            window.location.href = '/api/accounts/change-password/?required=true';
                        }, 1500);
                    } else {
                        // Clear the flag if it exists
                        localStorage.removeItem('requires_password_change');
                        showAlert('Login successful! Redirecting...', 'success');
                        
                        // Get redirect URL from query parameter or default to profile
                        const urlParams = new URLSearchParams(window.location.search);
                        const nextUrl = urlParams.get('next');
                        const redirectUrl = nextUrl && nextUrl.startsWith('/') 
                            ? nextUrl 
                            : '/api/accounts/user/profile/';
                        
                        // Verify tokens are stored
                        console.log('Tokens stored:', {
                            access: !!localStorage.getItem('access_token'),
                            refresh: !!localStorage.getItem('refresh_token'),
                            user: !!localStorage.getItem('user')
                        });
                        
                        // Redirect after short delay - use fetch to ensure token is sent
                        setTimeout(() => {
                            // First verify the token works by making a test request
                            const accessToken = localStorage.getItem('access_token');
                            const refreshToken = localStorage.getItem('refresh_token');
                            
                            if (accessToken && refreshToken) {
                                // Make a fetch request with proper headers to verify authentication
                                fetch(redirectUrl, {
                                    method: 'GET',
                                    headers: {
                                        'Authorization': `Bearer ${accessToken}`,
                                        'X-Refresh-Token': refreshToken,
                                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                                    }
                                }).then(response => {
                                    if (response.ok || response.redirected) {
                                        // If successful, navigate to the page
                                        window.location.href = redirectUrl;
                                    } else {
                                        // If failed, try redirecting anyway (token might work on server side)
                                        console.warn('Token verification failed, redirecting anyway');
                                        window.location.href = redirectUrl;
                                    }
                                }).catch(error => {
                                    console.error('Error verifying token:', error);
                                    // Redirect anyway
                                    window.location.href = redirectUrl;
                                });
                            } else {
                                // No tokens, redirect anyway (shouldn't happen)
                                console.error('No tokens found after login!');
                                window.location.href = redirectUrl;
                            }
                        }, 1000);
                    }
                } else {
                    // Handle validation errors
                    let errorMessage = 'Login failed. Please check your credentials.';
                    
                    // Extract error_code and message, handling both string and array formats
                    const errorCode = Array.isArray(data.error_code) ? data.error_code[0] : data.error_code;
                    const message = Array.isArray(data.message) ? data.message[0] : data.message;
                    
                    // Check for specific error codes first
                    if (errorCode === 'ACCOUNT_INACTIVE') {
                        errorMessage = message || 'Your account has been deactivated. Please contact the administrator for assistance.';
                    } else if (errorCode === 'INVALID_CREDENTIALS') {
                        errorMessage = message || 'Invalid username or password';
                    } else if (errorCode === 'MISSING_FIELDS') {
                        errorMessage = message || 'Username and password are required';
                    } else if (message) {
                        // Ensure message is a string, not an object
                        errorMessage = typeof message === 'string' ? message : (Array.isArray(message) ? message[0] : 'Invalid credentials');
                    } else if (data.username) {
                        errorMessage = Array.isArray(data.username) ? data.username[0] : (typeof data.username === 'string' ? data.username : 'Invalid username');
                    } else if (data.password) {
                        errorMessage = Array.isArray(data.password) ? data.password[0] : (typeof data.password === 'string' ? data.password : 'Invalid password');
                    } else if (data.non_field_errors) {
                        const nfe = data.non_field_errors;
                        if (Array.isArray(nfe) && nfe.length > 0) {
                            errorMessage = typeof nfe[0] === 'string' ? nfe[0] : 'Invalid credentials';
                        } else if (typeof nfe === 'string') {
                            errorMessage = nfe;
                        } else {
                            errorMessage = 'Invalid credentials';
                        }
                    } else if (data.detail) {
                        errorMessage = Array.isArray(data.detail) ? data.detail[0] : (typeof data.detail === 'string' ? data.detail : 'Invalid credentials');
                    } else {
                        // If we still don't have a message, use default
                        errorMessage = 'Invalid username or password';
                    }
                    
                    showAlert(errorMessage);
                    
                    // Re-enable submit button
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
            } catch (error) {
                console.error('Login error:', error);
                
                // Try to extract more specific error information
                let errorMessage = 'An error occurred. Please try again.';
                
                // Check if error has a response (network error)
                if (error.response) {
                    try {
                        const errorData = await error.response.json();
                        if (errorData.error_code) {
                            errorMessage = errorData.message || errorMessage;
                        } else if (errorData.message) {
                            errorMessage = errorData.message;
                        } else if (errorData.detail) {
                            errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Invalid credentials';
                        }
                    } catch (e) {
                        // If response is not JSON, try to get text
                        try {
                            const text = await error.response.text();
                            if (text) {
                                errorMessage = 'Server error: ' + text.substring(0, 100);
                            }
                        } catch (e2) {
                            // Use default message
                        }
                    }
                } else if (error.message) {
                    // Network error or other error
                    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                        errorMessage = 'Network error. Please check your connection and try again.';
                    } else {
                        errorMessage = error.message;
                    }
                }
                
                showAlert(errorMessage);
                
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.textContent = 'Sign In';
            }
        });
    }

    // Real-time validation
    usernameInput.addEventListener('blur', validateForm);
    passwordInput.addEventListener('blur', validateForm);
    
    // Clear errors on input
    usernameInput.addEventListener('input', function() {
        this.classList.remove('error');
        const errorMsg = this.parentElement.querySelector('.error-message');
        if (errorMsg) errorMsg.remove();
        hideAlert();
    });
    
    passwordInput.addEventListener('input', function() {
        this.classList.remove('error');
        const errorMsg = this.parentElement.querySelector('.error-message');
        if (errorMsg) errorMsg.remove();
        hideAlert();
    });
});

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
