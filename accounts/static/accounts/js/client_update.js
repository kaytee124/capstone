// Client update form handler
document.addEventListener('DOMContentLoaded', function() {
    loadProfile();
    setupForm();
});

async function loadProfile() {
    try {
        // Use global fetch which automatically handles tokens and refresh
        const response = await fetch('/api/accounts/user/profile/', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
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
            
            document.getElementById('username').value = user.username || '';
            document.getElementById('email').value = user.email || '';
            document.getElementById('first_name').value = user.first_name || '';
            document.getElementById('last_name').value = user.last_name || '';
            document.getElementById('phone_number').value = user.phone_number || '';
            document.getElementById('whatsapp_number').value = user.whatsapp_number || '';
            document.getElementById('address').value = user.address || '';
            document.getElementById('preferred_contact_method').value = user.preferred_contact_method || 'phone';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

function setupForm() {
    const form = document.getElementById('updateForm');
    
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
            preferred_contact_method: document.getElementById('preferred_contact_method').value
        };
        
        try {
            // Use global fetch which automatically handles tokens and refresh
            const response = await fetch('/api/accounts/client/update/', {
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
                // Update localStorage with new user data
                if (data.user) {
                    localStorage.setItem('user', JSON.stringify(data.user));
                    // Update username display in header
                    if (typeof window.updateUserNameDisplay === 'function') {
                        window.updateUserNameDisplay();
                    }
                }
                
                showAlert('Profile updated successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/api/accounts/user/profile/';
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to update profile', 'error');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            showAlert('An error occurred. Please try again.', 'error');
        }
    });
}

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
            <span>${message}</span>
        </div>
    `;
    alertContainer.classList.remove('hidden');
    
    setTimeout(() => {
        alertContainer.classList.add('hidden');
    }, 5000);
}
