// Error message extraction function
function extractErrorMessage(data) {
    if (typeof data === 'string') {
        try {
            data = JSON.parse(data);
        } catch (e) {
            return data;
        }
    }
    
    if (data.message) {
        if (Array.isArray(data.message)) {
            const msg = data.message[0];
            return typeof msg === 'string' ? msg : (msg?.string || String(msg));
        }
        if (typeof data.message === 'string') {
            return data.message;
        }
    }
    
    if (data.error_code) {
        const errorMessages = {
            'PHONE_EXISTS': 'Phone number already registered. Please use a different phone number.',
            'WHATSAPP_EXISTS': 'WhatsApp number already registered. Please use a different WhatsApp number.',
            'EMAIL_EXISTS': 'Email already registered. Please use a different email address.',
            'USERNAME_EXISTS': 'Username already taken. Please choose a different username.',
            'MISSING_FIELDS': 'Please fill in all required fields.',
            'INVALID_EMAIL': 'Invalid email format. Please enter a valid email address.',
            'INVALID_PASSWORD': 'Password must be at least 8 characters long.',
            'VALIDATION_ERROR': 'Please check the form for errors.'
        };
        
        if (errorMessages[data.error_code]) {
            return errorMessages[data.error_code];
        }
        if (data.message) {
            return data.message;
        }
    }
    
    // Helper to extract string from ErrorDetail or regular value
    function extractString(value) {
        if (value && typeof value === 'object') {
            if (value.string !== undefined) {
                return String(value.string);
            }
            if (value.message !== undefined) {
                return extractString(value.message);
            }
        }
        return String(value);
    }
    
    if (data.errors && typeof data.errors === 'object') {
        const fieldErrors = [];
        for (const [field, errors] of Object.entries(data.errors)) {
            if (Array.isArray(errors) && errors.length > 0) {
                const errorMsg = errors[0];
                const msg = extractString(errorMsg);
                if (msg) {
                    const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
                    fieldErrors.push(`${fieldName}: ${msg}`);
                }
            } else if (typeof errors === 'string') {
                const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
                fieldErrors.push(`${fieldName}: ${errors}`);
            } else if (errors && typeof errors === 'object') {
                let msg = '';
                // Check for custom error format with message/error_code
                if (errors.message) {
                    msg = extractString(errors.message);
                } else if (errors.error_code) {
                    // Map error code to user-friendly message
                    const errorMessages = {
                        'PHONE_EXISTS': 'Phone number already registered',
                        'WHATSAPP_EXISTS': 'WhatsApp number already registered',
                        'EMAIL_EXISTS': 'Email already registered',
                        'USERNAME_EXISTS': 'Username already taken'
                    };
                    msg = errorMessages[errors.error_code] || extractString(errors.error_code);
                } else if (errors.string) {
                    msg = extractString(errors.string);
                } else {
                    // Try to extract from the object itself
                    msg = extractString(errors);
                }
                if (msg && msg !== '[object Object]') {
                    fieldErrors.push(msg);
                }
            }
        }
        
        if (fieldErrors.length > 0) {
            return fieldErrors.join('. ');
        }
    }
    
    return data.message || 'An error occurred. Please try again.';
}

// Create customer form handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            phone_number: document.getElementById('phone_number').value,
            whatsapp_number: document.getElementById('whatsapp_number').value,
            address: document.getElementById('address').value,
            preferred_contact_method: document.getElementById('preferred_contact_method').value,
            notes: document.getElementById('notes').value || ''
        };
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const response = await fetch('/api/customers/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'X-Refresh-Token': localStorage.getItem('refresh_token') || ''
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Customer created successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/api/accounts/clients/';
                }, 1500);
            } else {
                const errorMessage = extractErrorMessage(data);
                showAlert(errorMessage, 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        } catch (error) {
            console.error('Error creating customer:', error);
            showAlert('An error occurred. Please try again.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
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
