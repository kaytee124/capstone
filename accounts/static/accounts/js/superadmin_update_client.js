// Superadmin Update Client - Load and update client details
document.addEventListener('DOMContentLoaded', function() {
    loadClientDetails();
    setupForm();
});

async function loadClientDetails() {
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
        showError('Invalid client ID');
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/superadmin/user/${userId}/`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Failed to load client details');
        }
        
        const data = await response.json();
        updateTokens(data);
        const user = data.user;
        
        document.getElementById('username').value = user.username || '';
        document.getElementById('first_name').value = user.first_name || '';
        document.getElementById('last_name').value = user.last_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('phone_number').value = user.phone_number || '';
        document.getElementById('whatsapp_number').value = user.whatsapp_number || '';
        document.getElementById('address').value = user.address || '';
        document.getElementById('preferred_contact_method').value = user.preferred_contact_method || 'phone';
        document.getElementById('is_active').value = (user.is_active || user.status === 'active') ? 'true' : 'false';
        document.getElementById('role').value = user.role || 'client';
        
    } catch (error) {
        console.error('Error loading client details:', error);
        showError('Failed to load client details. Please try again.');
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
            phone_number: document.getElementById('phone_number').value,
            whatsapp_number: document.getElementById('whatsapp_number').value,
            address: document.getElementById('address').value,
            preferred_contact_method: document.getElementById('preferred_contact_method').value,
            is_active: document.getElementById('is_active').value === 'true',
            role: document.getElementById('role').value
        };
        
        try {
            const response = await fetch(`/api/accounts/superadmin/client/${userId}/update/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            updateTokens(data);
            
            if (response.ok) {
                showAlert('Client updated successfully!', 'success');
                setTimeout(() => window.location.href = `/api/accounts/superadmin/user/${userId}/`, 1500);
            } else {
                showAlert(data.message || 'Failed to update client', 'error');
            }
        } catch (error) {
            console.error('Error updating client:', error);
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
