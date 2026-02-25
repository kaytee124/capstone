// Service create functionality
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
});

async function handleSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';
    
    try {
        const formData = {
            name: document.getElementById('name').value.trim(),
            category: document.getElementById('category').value.trim(),
            price: parseFloat(document.getElementById('price').value),
            unit: document.getElementById('unit').value.trim(),
            estimated_days: parseInt(document.getElementById('estimated_days').value) || 2,
            is_active: document.getElementById('is_active').value === 'true',
            description: document.getElementById('description').value.trim()
        };
        
        const response = await fetch('/api/services/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Success
            showAlert('Service created successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/api/services/list/';
            }, 1500);
        } else {
            // Handle errors
            console.log('Error response data:', data); // Debug log
            const errorMessage = extractErrorMessage(data);
            console.log('Extracted error message:', errorMessage); // Debug log
            showAlert(errorMessage, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error creating service:', error);
        showAlert('An error occurred. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function extractErrorMessage(data) {
    // If data is a string, try to parse it
    if (typeof data === 'string') {
        try {
            data = JSON.parse(data);
        } catch (e) {
            return data; // Return the string if it can't be parsed
        }
    }
    
    // Handle custom error format with error_code
    if (data.error_code) {
        return data.message || 'An error occurred';
    }
    
    // Handle standard error message
    if (data.message) {
        if (Array.isArray(data.message)) {
            const msg = data.message[0];
            if (typeof msg === 'string') {
                return msg;
            }
            if (msg && typeof msg === 'object') {
                return msg.string || msg.message || msg.detail || JSON.stringify(msg);
            }
            return String(msg);
        }
        if (typeof data.message === 'string') {
            return data.message;
        }
    }
    
    // Handle field-level validation errors (e.g., {'field': [ErrorDetail(...)]})
    const fieldErrors = [];
    for (const [field, errors] of Object.entries(data)) {
        // Skip non-error fields
        if (field === 'error_code' || field === 'status_code' || field === 'message' || field === 'detail') {
            continue;
        }
        
        if (Array.isArray(errors) && errors.length > 0) {
            // DRF serializes ErrorDetail objects as strings in JSON
            // So errors[0] should already be a string like "This field may not be blank."
            const errorMsg = errors[0];
            let msg = '';
            
            // Most common case: ErrorDetail is serialized as a string
            if (typeof errorMsg === 'string') {
                msg = errorMsg;
            } 
            // If it's an object (shouldn't happen with DRF JSON, but handle it)
            else if (errorMsg && typeof errorMsg === 'object') {
                // Try to get the string property directly
                msg = errorMsg.string || errorMsg.message || errorMsg.detail || '';
                // If still empty, try to extract from string representation
                if (!msg) {
                    const objStr = String(errorMsg);
                    const match = objStr.match(/string=['"]([^'"]+)['"]/);
                    msg = match ? match[1] : '';
                }
            } 
            // Fallback to string conversion
            else {
                msg = String(errorMsg);
            }
            
            // Only add if we have a message
            if (msg) {
                const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
                fieldErrors.push(`${fieldName}: ${msg}`);
            }
        } else if (typeof errors === 'string') {
            const fieldName = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
            fieldErrors.push(`${fieldName}: ${errors}`);
        }
    }
    
    if (fieldErrors.length > 0) {
        return fieldErrors.join('. ');
    }
    
    // Fallback - try to stringify the data to see what we got
    try {
        const dataStr = JSON.stringify(data);
        // If it's just an empty object or something we can't parse, return generic message
        if (dataStr === '{}' || dataStr === '[]') {
            return 'Failed to create service. Please check your input.';
        }
        // Otherwise return a formatted version
        return dataStr;
    } catch (e) {
        return 'Failed to create service. Please check your input.';
    }
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                <span>${type === 'error' ? '✕' : '✓'}</span>
                <span>${message}</span>
            </div>
        `;
        alertContainer.classList.remove('hidden');
        
        if (type === 'success') {
            setTimeout(() => {
                alertContainer.classList.add('hidden');
            }, 3000);
        }
    }
}

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
