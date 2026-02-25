// Staff Update Client - Load and update client details
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
        // Use global fetch which automatically handles tokens and refresh
        const response = await fetch(`/api/accounts/staff/user/${userId}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Failed to load client details');
        }
        
        const data = await response.json();
        
        // Check if tokens were refreshed and update them
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
        
        const user = data.user;
        
        // Populate form fields
        const usernameField = document.getElementById('username');
        if (usernameField) usernameField.value = user.username || '';
        document.getElementById('first_name').value = user.first_name || '';
        document.getElementById('last_name').value = user.last_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('phone_number').value = user.phone_number || '';
        document.getElementById('whatsapp_number').value = user.whatsapp_number || '';
        document.getElementById('address').value = user.address || '';
        document.getElementById('preferred_contact_method').value = user.preferred_contact_method || 'phone';
        
        // Set status
        const status = user.status !== undefined ? user.status : (user.is_active ? 'active' : 'inactive');
        document.getElementById('is_active').value = (status === 'active' || user.is_active === true) ? 'true' : 'false';
        
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
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            email: document.getElementById('email').value,
            phone_number: document.getElementById('phone_number').value,
            whatsapp_number: document.getElementById('whatsapp_number').value,
            address: document.getElementById('address').value,
            preferred_contact_method: document.getElementById('preferred_contact_method').value,
            is_active: document.getElementById('is_active').value === 'true'
        };
        
        // Username is read-only and should not be sent
        
        try {
            // Use global fetch which automatically handles tokens and refresh
            const response = await fetch(`/api/accounts/staff/client/${userId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            // Check if tokens were refreshed and update them
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
            
            if (response.ok) {
                showAlert('Client updated successfully!', 'success');
                setTimeout(() => {
                    window.location.href = `/api/accounts/staff/user/${userId}/`;
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to update client', 'error');
            }
        } catch (error) {
            console.error('Error updating client:', error);
            showAlert('An error occurred. Please try again.', 'error');
        }
    });
}

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        // Create alert container if it doesn't exist
        const formCard = document.querySelector('.form-card');
        if (formCard) {
            const container = document.createElement('div');
            container.id = 'alertContainer';
            container.className = 'alert-container';
            formCard.insertBefore(container, formCard.firstChild);
        }
    }
    
    const container = document.getElementById('alertContainer');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-${type}">
                <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
                <span>${message}</span>
            </div>
        `;
        container.classList.remove('hidden');
        
        if (type === 'success') {
            setTimeout(() => {
                container.classList.add('hidden');
            }, 5000);
        }
    }
}

function showError(message) {
    showAlert(message, 'error');
}
