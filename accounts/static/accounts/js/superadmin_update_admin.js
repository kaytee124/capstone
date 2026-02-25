// Superadmin Update Admin - Load and update admin details
document.addEventListener('DOMContentLoaded', function() {
    loadAdminDetails();
    setupForm();
});

async function loadAdminDetails() {
    // Get user_id from URL - find the number in the path
    const pathParts = window.location.pathname.split('/').filter(part => part !== '');
    let userId = null;
    
    // Find the user ID in the path (should be a number)
    for (let i = pathParts.length - 1; i >= 0; i--) {
        if (!isNaN(pathParts[i]) && pathParts[i] !== '') {
            userId = pathParts[i];
            break;
        }
    }
    
    if (!userId || isNaN(userId)) {
        showError('Invalid admin ID');
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/superadmin/user/${userId}/`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Failed to load admin details');
        }
        
        const data = await response.json();
        updateTokens(data);
        const user = data.user;
        
        document.getElementById('username').value = user.username || '';
        document.getElementById('first_name').value = user.first_name || '';
        document.getElementById('last_name').value = user.last_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('is_active').value = (user.is_active || user.status === 'active') ? 'true' : 'false';
        document.getElementById('role').value = user.role || 'admin';
        
        // Show/hide client option based on whether user has customer profile
        const clientOption = document.getElementById('clientRoleOption');
        if (clientOption) {
            if (user.has_customer_profile) {
                clientOption.style.display = 'block';
            } else {
                clientOption.style.display = 'none';
                // If current role is client but no customer profile, this shouldn't happen, but handle it
                if (user.role === 'client') {
                    clientOption.style.display = 'block';
                }
            }
        }
        
    } catch (error) {
        console.error('Error loading admin details:', error);
        showError('Failed to load admin details. Please try again.');
    }
}

function setupForm() {
    const form = document.getElementById('updateForm');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get user_id from URL - find the number in the path
        const pathParts = window.location.pathname.split('/').filter(part => part !== '');
        let userId = null;
        
        // Find the user ID in the path (should be a number)
        for (let i = pathParts.length - 1; i >= 0; i--) {
            if (!isNaN(pathParts[i]) && pathParts[i] !== '') {
                userId = pathParts[i];
                break;
            }
        }
        
        const formData = {
            // Username is read-only and should not be sent
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            email: document.getElementById('email').value,
            is_active: document.getElementById('is_active').value === 'true',
            role: document.getElementById('role').value
        };
        
        try {
            const response = await fetch(`/api/accounts/superadmin/admin/${userId}/update/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            updateTokens(data);
            
            if (response.ok) {
                showAlert('Admin updated successfully!', 'success');
                setTimeout(() => window.location.href = `/api/accounts/superadmin/user/${userId}/`, 1500);
            } else {
                // Handle validation errors
                let errorMessage = data.message || 'Failed to update admin';
                
                // Check for role conversion error
                if (data.role) {
                    errorMessage = Array.isArray(data.role) ? data.role[0] : data.role;
                } else if (data.customer_data_required) {
                    errorMessage = Array.isArray(data.customer_data_required) ? data.customer_data_required[0] : data.customer_data_required;
                } else if (data.non_field_errors) {
                    errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
                }
                
                showAlert(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error updating admin:', error);
            showAlert('An error occurred. Please try again.', 'error');
        }
    });
}

function updateTokens(data) {
    if (data.token_refreshed && data.new_access_token) {
        if (typeof TokenManager !== 'undefined') {
            TokenManager.setAccessToken(data.new_access_token);
            if (data.new_refresh_token) TokenManager.setRefreshToken(data.new_refresh_token);
        } else {
            localStorage.setItem('access_token', data.new_access_token);
            if (data.new_refresh_token) localStorage.setItem('refresh_token', data.new_refresh_token);
        }
    }
}

function showAlert(message, type = 'error') {
    let container = document.getElementById('alertContainer');
    if (!container) {
        const formCard = document.querySelector('.form-card');
        if (formCard) {
            container = document.createElement('div');
            container.id = 'alertContainer';
            container.className = 'alert-container';
            formCard.insertBefore(container, formCard.firstChild);
        }
    }
    if (container) {
        container.innerHTML = `<div class="alert alert-${type}"><span>${type === 'error' ? '✕' : '✓'}</span><span>${message}</span></div>`;
        container.classList.remove('hidden');
        if (type === 'success') setTimeout(() => container.classList.add('hidden'), 5000);
    }
}

function showError(message) { showAlert(message, 'error'); }
