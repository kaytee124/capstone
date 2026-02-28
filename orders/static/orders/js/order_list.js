// Orders list functionality
let orderStatusFilter = '';
let paymentStatusFilter = '';

document.addEventListener('DOMContentLoaded', function() {
    loadOrders();
    setupEventListeners();
    checkUserRole();
});

function checkUserRole() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            // Show create button only for admin, superadmin, and employee
            if (user.role && ['admin', 'superadmin', 'employee'].includes(user.role)) {
                const createBtn = document.getElementById('createOrderBtn');
                if (createBtn) {
                    createBtn.style.display = 'inline-block';
                    createBtn.href = '/api/orders/create/';
                }
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }
}

function setupEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', function() {
        orderStatusFilter = document.getElementById('orderStatusFilter').value;
        paymentStatusFilter = document.getElementById('paymentStatusFilter').value;
        loadOrders();
    });
    
    document.getElementById('orderStatusFilter').addEventListener('change', function() {
        orderStatusFilter = this.value;
        loadOrders();
    });
    
    document.getElementById('paymentStatusFilter').addEventListener('change', function() {
        paymentStatusFilter = this.value;
        loadOrders();
    });
}

async function loadOrders() {
    try {
        const params = new URLSearchParams();
        if (orderStatusFilter) params.append('order_status', orderStatusFilter);
        if (paymentStatusFilter) params.append('payment_status', paymentStatusFilter);
        
        const response = await fetch(`/api/orders/list/?${params}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to load orders');
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
        
        renderOrders(data.data || []);
    } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('ordersTableBody').innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 2rem; color: #ef4444;">
                    Failed to load orders. Please try again.
                </td>
            </tr>
        `;
    }
}

function renderOrders(orders) {
    const tbody = document.getElementById('ordersTableBody');
    
    if (orders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 2rem;">No orders found</td>
            </tr>
        `;
        return;
    }
    
    // Check user role to show update button
    const userStr = localStorage.getItem('user');
    let userRole = null;
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            userRole = user.role;
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }
    
    const canUpdate = userRole && ['admin', 'superadmin', 'employee'].includes(userRole);
    
    tbody.innerHTML = orders.map(order => {
        const orderStatusClass = `status-${order.order_status.replace('_', '-')}`;
        const paymentStatusClass = `payment-${order.payment_status.replace('_', '-')}`;
        const createdDate = order.created_at ? new Date(order.created_at).toLocaleDateString() : '-';
        
        const updateButton = canUpdate 
            ? `<a href="/api/orders/${order.id}/update/" class="btn btn-sm btn-primary">Update</a>`
            : '';
        
        return `
            <tr>
                <td>${order.order_number || '-'}</td>
                <td>${order.customer_username || order.customer_name || '-'}</td>
                <td>₦${parseFloat(order.total_amount || 0).toFixed(2)}</td>
                <td>₦${parseFloat(order.amount_paid || 0).toFixed(2)}</td>
                <td>
                    <span class="status-badge ${orderStatusClass}">
                        ${formatStatus(order.order_status)}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${paymentStatusClass}">
                        ${formatPaymentStatus(order.payment_status)}
                    </span>
                </td>
                <td>${createdDate}</td>
                <td>
                    <div class="action-buttons">
                        <a href="/api/orders/${order.id}/" class="btn btn-sm btn-secondary">View</a>
                        ${updateButton}
                        <button onclick="handleMakePayment(${order.id})" class="btn btn-sm btn-primary">Make Payment</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function formatStatus(status) {
    const statusMap = {
        'pending': 'Pending',
        'in_progress': 'In Progress',
        'ready': 'Ready',
        'completed': 'Completed',
        'cancelled': 'Cancelled'
    };
    return statusMap[status] || status;
}

function formatPaymentStatus(status) {
    const statusMap = {
        'pending': 'Pending',
        'partially_paid': 'Partially Paid',
        'paid': 'Paid'
    };
    return statusMap[status] || status;
}

function handleMakePayment(orderId) {
    // Placeholder function - will be implemented later
    showAlert('Make Payment functionality will be implemented soon', 'info');
}

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
                <span>${message}</span>
            </div>
        `;
        alertContainer.classList.remove('hidden');
        
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                alertContainer.classList.add('hidden');
            }, 3000);
        }
    }
}
