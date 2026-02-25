// Staff User By ID - Load and display user details
document.addEventListener('DOMContentLoaded', function() {
    loadUserDetails();
});

async function loadUserDetails() {
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
        showError('Invalid user ID');
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
            throw new Error(errorData.message || 'Failed to load user details');
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
        
        // Display user information
        document.getElementById('profileName').textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'N/A';
        document.getElementById('profileEmail').textContent = user.email || 'N/A';
        
        // Status badge
        const statusBadge = document.getElementById('profileStatus');
        // Check if status field exists, otherwise use is_active
        const status = user.status !== undefined ? user.status : (user.is_active ? 'active' : 'inactive');
        statusBadge.textContent = status;
        statusBadge.className = `status-badge ${status}`;
        
        // Personal information
        document.getElementById('firstName').textContent = user.first_name || '-';
        document.getElementById('lastName').textContent = user.last_name || '-';
        document.getElementById('username').textContent = user.username || '-';
        document.getElementById('email').textContent = user.email || '-';
        document.getElementById('status').textContent = status.charAt(0).toUpperCase() + status.slice(1);
        document.getElementById('updatedBy').textContent = user.updated_by_name || '-';
        
        // Customer information (if client) - only show if user is a client
        if (user.role === 'client' && (user.phone_number !== undefined || user.whatsapp_number !== undefined || user.address !== undefined)) {
            const customerSection = document.getElementById('customerSection');
            if (customerSection) {
                customerSection.style.display = 'block';
                
                document.getElementById('phoneNumber').textContent = user.phone_number || '-';
                document.getElementById('whatsappNumber').textContent = user.whatsapp_number || '-';
                document.getElementById('address').textContent = user.address || '-';
                document.getElementById('preferredContact').textContent = user.preferred_contact_method || '-';
                document.getElementById('notes').textContent = user.notes || 'no note';
                document.getElementById('customerCreatedBy').textContent = user.customer_created_by_name || '-';
                document.getElementById('customerUpdatedBy').textContent = user.customer_updated_by_name || '-';
                document.getElementById('totalOrders').textContent = user.total_orders || 0;
                document.getElementById('totalSpent').textContent = user.total_spent ? `$${user.total_spent}` : '$0.00';
                document.getElementById('lastOrderDate').textContent = user.last_order_date ? new Date(user.last_order_date).toLocaleDateString() : '-';
            }
        } else {
            // Hide customer section if user is not a client
            const customerSection = document.getElementById('customerSection');
            if (customerSection) {
                customerSection.style.display = 'none';
            }
        }
        
        // Show update button based on user role and current user's role
        const updateBtn = document.getElementById('updateBtn');
        if (updateBtn && user.role) {
            const userData = localStorage.getItem('user');
            let currentUserRole = null;
            if (userData) {
                try {
                    currentUserRole = JSON.parse(userData).role;
                } catch (e) {
                    console.error('Error parsing user data:', e);
                }
            }
            
            if (user.role === 'client') {
                // Use superadmin URL if current user is superadmin, otherwise use staff URL
                if (currentUserRole === 'superadmin') {
                    updateBtn.href = `/api/accounts/superadmin/client/${userId}/update/`;
                } else {
                    updateBtn.href = `/api/accounts/staff/client/${userId}/update/`;
                }
                updateBtn.style.display = 'inline-block';
            } else if (user.role === 'employee') {
                // Check if current user is admin or superadmin
                if (currentUserRole === 'superadmin') {
                    updateBtn.href = `/api/accounts/superadmin/employee/${userId}/update/`;
                } else if (currentUserRole === 'admin') {
                    updateBtn.href = `/api/accounts/admin/employee/${userId}/update/`;
                }
                if (currentUserRole === 'admin' || currentUserRole === 'superadmin') {
                    updateBtn.style.display = 'inline-block';
                }
            }
        }
        
    } catch (error) {
        console.error('Error loading user details:', error);
        showError('Failed to load user details. Please try again.');
    }
}

function showError(message) {
    const alertContainer = document.querySelector('#alertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-error">
                <span>✕</span>
                <span>${message}</span>
            </div>
        `;
        alertContainer.classList.remove('hidden');
    } else {
        alert(message);
    }
}
