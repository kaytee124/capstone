// Change Password Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    const oldPasswordInput = document.getElementById('oldPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const oldPasswordToggle = document.getElementById('oldPasswordToggle');
    const newPasswordToggle = document.getElementById('newPasswordToggle');
    const confirmPasswordToggle = document.getElementById('confirmPasswordToggle');
    const alertContainer = document.getElementById('alertContainer');
    const submitBtn = document.getElementById('submitBtn');
    const passwordStrengthBar = document.getElementById('passwordStrengthBar');
    const passwordMatchIndicator = document.getElementById('passwordMatchIndicator');
    
    // Check if password change is required
    const urlParams = new URLSearchParams(window.location.search);
    const isRequired = urlParams.get('required') === 'true' || localStorage.getItem('requires_password_change') === 'true';
    
    // Hide/disable back link if password change is required
    const backLink = document.querySelector('.back-link');
    if (backLink && isRequired) {
        backLink.style.display = 'none';
        // Show warning message
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-error">
                    <span>⚠</span>
                    <span>You must change your default password before you can access other pages.</span>
                </div>
            `;
            alertContainer.classList.remove('hidden');
        }
    }
    
    // Prevent navigation if password change is required
    let allowRedirect = false;
    let beforeUnloadHandler = null;
    let clickHandler = null;
    
    if (isRequired) {
        // Prevent navigation using beforeunload
        beforeUnloadHandler = function(e) {
            if (!allowRedirect) {
                e.preventDefault();
                e.returnValue = 'Please change your password before navigating away.';
                return e.returnValue;
            }
        };
        window.addEventListener('beforeunload', beforeUnloadHandler);
        
        // Prevent link navigation
        clickHandler = function(e) {
            if (!allowRedirect) {
                const link = e.target.closest('a');
                if (link && link.href && !link.href.includes('change-password')) {
                    e.preventDefault();
                    alert('Please change your password before navigating to other pages.');
                    return false;
                }
            }
        };
        document.addEventListener('click', clickHandler, true);
    }

    // Get access token from localStorage
    function getAccessToken() {
        return localStorage.getItem('access_token');
    }

    // Password toggle functionality
    function setupPasswordToggle(toggleBtn, input) {
        if (toggleBtn && input) {
            toggleBtn.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                
                const icon = toggleBtn.querySelector('svg');
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
    }

    setupPasswordToggle(oldPasswordToggle, oldPasswordInput);
    setupPasswordToggle(newPasswordToggle, newPasswordInput);
    setupPasswordToggle(confirmPasswordToggle, confirmPasswordInput);

    // Password strength checker
    function checkPasswordStrength(password) {
        let strength = 0;
        
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z\d]/.test(password)) strength++;
        
        return strength;
    }

    function updatePasswordStrength(password) {
        if (!passwordStrengthBar) return;
        
        const strength = checkPasswordStrength(password);
        passwordStrengthBar.className = 'password-strength-bar';
        
        if (password.length === 0) {
            passwordStrengthBar.style.width = '0%';
            passwordStrengthBar.style.backgroundColor = '';
            return;
        }
        
        // Calculate width percentage based on strength (0-5 scale)
        const widthPercentage = (strength / 5) * 100;
        passwordStrengthBar.style.width = widthPercentage + '%';
        
        // Set color based on strength
        if (strength <= 2) {
            passwordStrengthBar.style.backgroundColor = 'var(--error-color, #dc3545)';
        } else if (strength <= 3) {
            passwordStrengthBar.style.backgroundColor = 'var(--warning-color, #ffc107)';
        } else {
            passwordStrengthBar.style.backgroundColor = 'var(--success-color, #28a745)';
        }
    }

    // Password match checker
    function checkPasswordMatch() {
        if (!confirmPasswordInput || !passwordMatchIndicator) return;
        
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword.length === 0) {
            passwordMatchIndicator.classList.add('hidden');
            return;
        }
        
        passwordMatchIndicator.classList.remove('hidden');
        
        if (newPassword === confirmPassword) {
            passwordMatchIndicator.className = 'password-match-indicator match';
            passwordMatchIndicator.innerHTML = '✓ Passwords match';
            confirmPasswordInput.classList.remove('error');
            confirmPasswordInput.classList.add('success');
        } else {
            passwordMatchIndicator.className = 'password-match-indicator no-match';
            passwordMatchIndicator.innerHTML = '✕ Passwords do not match';
            confirmPasswordInput.classList.remove('success');
            confirmPasswordInput.classList.add('error');
        }
    }

    // Update password requirements
    function updatePasswordRequirements() {
        const password = newPasswordInput.value;
        const requirements = document.querySelectorAll('.password-requirements-list li');
        
        requirements.forEach(req => {
            const text = req.textContent.trim();
            let isValid = false;
            
            if (text.includes('8 characters')) {
                isValid = password.length >= 8;
            } else if (text.includes('uppercase')) {
                isValid = /[A-Z]/.test(password);
            } else if (text.includes('lowercase')) {
                isValid = /[a-z]/.test(password);
            } else if (text.includes('number')) {
                isValid = /\d/.test(password);
            } else if (text.includes('special character')) {
                isValid = /[^a-zA-Z\d]/.test(password);
            }
            
            if (isValid) {
                req.classList.add('valid');
            } else {
                req.classList.remove('valid');
            }
        });
    }

    // Form validation
    function validateForm() {
        let isValid = true;
        clearErrors();
        
        // Validate old password
        if (!oldPasswordInput.value) {
            showFieldError(oldPasswordInput, 'Old password is required');
            isValid = false;
        }
        
        // Validate new password
        if (!newPasswordInput.value) {
            showFieldError(newPasswordInput, 'New password is required');
            isValid = false;
        } else if (newPasswordInput.value.length < 8) {
            showFieldError(newPasswordInput, 'New password must be at least 8 characters');
            isValid = false;
        }
        
        // Validate confirm password
        if (!confirmPasswordInput.value) {
            showFieldError(confirmPasswordInput, 'Please confirm your new password');
            isValid = false;
        } else if (newPasswordInput.value !== confirmPasswordInput.value) {
            showFieldError(confirmPasswordInput, 'Passwords do not match');
            isValid = false;
        }
        
        // Check if old and new passwords are the same
        if (oldPasswordInput.value && newPasswordInput.value && 
            oldPasswordInput.value === newPasswordInput.value) {
            showFieldError(newPasswordInput, 'New password must be different from old password');
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
        document.querySelectorAll('.success').forEach(el => el.classList.remove('success'));
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
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!validateForm()) {
                return;
            }
            
            const accessToken = getAccessToken();
            if (!accessToken) {
                showAlert('You must be logged in to change your password. Redirecting to login...');
                setTimeout(() => {
                    window.location.href = '/api/accounts/login/';
                }, 2000);
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Changing password...';
            
            try {
                // Use global fetch which automatically handles tokens and refresh
                const response = await fetch('/api/accounts/change-password/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        old_password: oldPasswordInput.value,
                        new_password: newPasswordInput.value,
                        confirm_password: confirmPasswordInput.value
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Check for auto-refreshed tokens and update localStorage
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
                    
                    // Clear the requires_password_change flag
                    localStorage.removeItem('requires_password_change');
                    
                    showAlert('Password changed successfully!', 'success');
                    changePasswordForm.reset();
                    updatePasswordStrength('');
                    passwordMatchIndicator.classList.add('hidden');
                    
                    // Allow redirect after successful password change
                    if (isRequired) {
                        allowRedirect = true;
                        // Remove event listeners
                        if (beforeUnloadHandler) {
                            window.removeEventListener('beforeunload', beforeUnloadHandler);
                        }
                        if (clickHandler) {
                            document.removeEventListener('click', clickHandler, true);
                        }
                    }
                    
                    // Always redirect to profile page after password change
                    setTimeout(() => {
                        // Use location.assign to ensure redirect works
                        window.location.assign('/api/accounts/user/profile/');
                    }, 2000);
                } else {
                    let errorMessage = 'Failed to change password. Please try again.';
                    
                    if (data.old_password) {
                        errorMessage = Array.isArray(data.old_password) ? data.old_password[0] : data.old_password;
                    } else if (data.new_password) {
                        errorMessage = Array.isArray(data.new_password) ? data.new_password[0] : data.new_password;
                    } else if (data.confirm_password) {
                        errorMessage = Array.isArray(data.confirm_password) ? data.confirm_password[0] : data.confirm_password;
                    } else if (data.non_field_errors) {
                        errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
                    } else if (data.detail) {
                        errorMessage = data.detail;
                    }
                    
                    showAlert(errorMessage);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Change Password';
                }
            } catch (error) {
                console.error('Change password error:', error);
                showAlert('An error occurred. Please try again.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Change Password';
            }
        });
    }

    // Real-time validation
    newPasswordInput.addEventListener('input', function() {
        this.classList.remove('error');
        const errorMsg = this.parentElement.querySelector('.error-message');
        if (errorMsg) errorMsg.remove();
        updatePasswordStrength(this.value);
        updatePasswordRequirements();
        checkPasswordMatch();
        hideAlert();
    });
    
    confirmPasswordInput.addEventListener('input', function() {
        this.classList.remove('error');
        const errorMsg = this.parentElement.querySelector('.error-message');
        if (errorMsg) errorMsg.remove();
        checkPasswordMatch();
        hideAlert();
    });
    
    oldPasswordInput.addEventListener('input', function() {
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
