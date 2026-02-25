// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Show error message if present in URL
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const errorMessage = urlParams.get('message');
    
    if (error && errorMessage) {
        const alertContainer = document.getElementById('alertContainer');
        const existingAlert = alertContainer.querySelector('.alert');
        if (!existingAlert) {
            showAlert(errorMessage, 'error');
        } else {
            alertContainer.classList.remove('hidden');
        }
    }
    
    loadProfile();
});

async function loadProfile() {
    try {
        // Get tokens - use TokenManager if available, otherwise localStorage
        const accessToken = typeof TokenManager !== 'undefined' 
            ? TokenManager.getAccessToken() 
            : localStorage.getItem('access_token');
        const refreshToken = typeof TokenManager !== 'undefined' 
            ? TokenManager.getRefreshToken() 
            : localStorage.getItem('refresh_token');
        
        if (!accessToken) {
            throw new Error('No access token found. Please log in again.');
        }
        
        // Use fetch with Accept header to get JSON response
        // The api.js interceptor will automatically add Authorization header, but we'll add it explicitly too
        const response = await fetch('/api/accounts/user/profile/', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
                'X-Refresh-Token': refreshToken || ''
            }
        });

        if (!response.ok) {
            // Try to get error message from response
            let errorMessage = 'Failed to load profile';
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || errorData.error_code || errorMessage;
            } catch (e) {
                // If response is not JSON, try to get status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        const user = data.user;
        
        if (!user) {
            throw new Error('No user data received');
        }

        // Update user info
        document.getElementById('profileName').textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'User';
        document.getElementById('profileEmail').textContent = user.email || '-';
        document.getElementById('firstName').textContent = user.first_name || '-';
        document.getElementById('lastName').textContent = user.last_name || '-';
        document.getElementById('username').textContent = user.username || '-';
        document.getElementById('email').textContent = user.email || '-';
        
        // Status
        const status = user.status || 'inactive';
        document.getElementById('status').textContent = status.charAt(0).toUpperCase() + status.slice(1);
        document.getElementById('profileStatus').textContent = status.charAt(0).toUpperCase() + status.slice(1);
        document.getElementById('profileStatus').className = `status-badge ${status}`;
        
        // Updated By
        document.getElementById('updatedBy').textContent = user.updated_by_name || '-';

        // Customer fields - show section if user is a client (check role from localStorage or if any customer field exists)
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        const isClient = userData.role === 'client';
        
        // Show customer section if user is a client (even if fields are null/empty)
        if (isClient) {
            document.getElementById('customerSection').style.display = 'block';
            document.getElementById('phoneNumber').textContent = user.phone_number || '-';
            document.getElementById('whatsappNumber').textContent = user.whatsapp_number || '-';
            document.getElementById('address').textContent = user.address || '-';
            document.getElementById('preferredContact').textContent = user.preferred_contact_method || '-';
            document.getElementById('notes').textContent = user.notes || 'no note';
            document.getElementById('customerCreatedBy').textContent = user.customer_created_by_name || '-';
            document.getElementById('customerUpdatedBy').textContent = user.customer_updated_by_name || '-';
            document.getElementById('totalOrders').textContent = user.total_orders !== undefined ? user.total_orders : 0;
            document.getElementById('totalSpent').textContent = user.total_spent ? `$${user.total_spent}` : '$0.00';
            document.getElementById('lastOrderDate').textContent = user.last_order_date ? new Date(user.last_order_date).toLocaleDateString() : '-';
        }

        // Show update button for clients
        if (isClient) {
            document.getElementById('updateBtn').style.display = 'inline-block';
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            tokens: {
                access: !!localStorage.getItem('access_token'),
                refresh: !!localStorage.getItem('refresh_token'),
                user: !!localStorage.getItem('user')
            }
        });
        showAlert(error.message || 'Failed to load profile. Please try again.', 'error');
    }
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
