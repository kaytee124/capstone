// Order detail functionality
document.addEventListener('DOMContentLoaded', function() {
    const urlParts = window.location.pathname.split('/').filter(p => p);
    const orderId = urlParts[urlParts.length - 1];
    
    if (orderId) {
        loadOrderDetail(orderId);
    } else {
        showError('Order ID not found in URL');
    }
});

async function loadOrderDetail(orderId) {
    try {
        const response = await fetch(`/api/orders/${orderId}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to load order');
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
        
        renderOrderDetail(data.data);
        checkUserRoleForButtons();
        
    } catch (error) {
        console.error('Error loading order:', error);
        showError('Failed to load order details. Please try again.');
    }
}

function renderOrderDetail(order) {
    document.getElementById('orderNumber').textContent = order.order_number || 'N/A';
    document.getElementById('orderNumberDetail').textContent = order.order_number || '-';
    document.getElementById('customerName').textContent = order.customer_name || order.customer_username || 'N/A';
    document.getElementById('customer').textContent = order.customer_name || order.customer_username || '-';
    document.getElementById('assignedTo').textContent = order.assigned_to_username || 'Not assigned';
    
    // Order status
    const orderStatus = formatStatus(order.order_status);
    document.getElementById('orderStatus').textContent = orderStatus;
    const orderStatusBadge = document.getElementById('orderStatusBadge');
    orderStatusBadge.textContent = orderStatus;
    orderStatusBadge.className = `status-badge status-${order.order_status.replace('_', '-')}`;
    
    // Payment status
    const paymentStatus = formatPaymentStatus(order.payment_status);
    document.getElementById('paymentStatus').textContent = paymentStatus;
    const paymentStatusBadge = document.getElementById('paymentStatusBadge');
    paymentStatusBadge.textContent = paymentStatus;
    paymentStatusBadge.className = `status-badge payment-${order.payment_status.replace('_', '-')}`;
    
    document.getElementById('totalAmount').textContent = `₦${parseFloat(order.total_amount || 0).toFixed(2)}`;
    document.getElementById('amountPaid').textContent = `₦${parseFloat(order.amount_paid || 0).toFixed(2)}`;
    document.getElementById('discountAmount').textContent = `₦${parseFloat(order.discount_amount || 0).toFixed(2)}`;
    document.getElementById('pickupDate').textContent = order.pickup_date ? new Date(order.pickup_date).toLocaleDateString() : '-';
    document.getElementById('deliveryDate').textContent = order.delivery_date ? new Date(order.delivery_date).toLocaleDateString() : '-';
    document.getElementById('estimatedCompletionDate').textContent = order.estimated_completion_date ? new Date(order.estimated_completion_date).toLocaleDateString() : '-';
    document.getElementById('completedAt').textContent = order.completed_at ? new Date(order.completed_at).toLocaleDateString() : '-';
    document.getElementById('deliveryNotes').textContent = order.delivery_notes || '-';
    document.getElementById('specialInstructions').textContent = order.special_instructions || '-';
    document.getElementById('createdAt').textContent = order.created_at ? new Date(order.created_at).toLocaleDateString() : '-';
    document.getElementById('createdBy').textContent = order.created_by_username || '-';
    
    // Render order items
    renderOrderItems(order.order_items || []);
}

function renderOrderItems(orderItems) {
    const itemsSection = document.getElementById('orderItemsSection');
    const itemsTableBody = document.getElementById('orderItemsTableBody');
    const itemsTableFooter = document.getElementById('orderItemsTableFooter');
    
    if (!itemsSection || !itemsTableBody) return;
    
    if (orderItems && orderItems.length > 0) {
        itemsSection.style.display = 'block';
        itemsTableBody.innerHTML = '';
        
        let totalAmount = 0;
        
        orderItems.forEach((item, index) => {
            const row = document.createElement('tr');
            const subtotal = parseFloat(item.subtotal || 0);
            totalAmount += subtotal;
            
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.service_name || '-'}</td>
                <td>${item.item_name || '-'}</td>
                <td>${item.quantity || 0}</td>
                <td>₦${parseFloat(item.unit_price || 0).toFixed(2)}</td>
                <td>₦${subtotal.toFixed(2)}</td>
                <td title="${item.notes || ''}">${item.notes || '-'}</td>
            `;
            itemsTableBody.appendChild(row);
        });
        
        // Show footer with total
        if (itemsTableFooter) {
            const totalCell = document.getElementById('orderItemsTotal');
            if (totalCell) {
                totalCell.textContent = `₦${totalAmount.toFixed(2)}`;
            }
            itemsTableFooter.style.display = 'table-row';
        }
    } else {
        itemsSection.style.display = 'none';
        if (itemsTableFooter) {
            itemsTableFooter.style.display = 'none';
        }
    }
}

function checkUserRoleForButtons() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            // Show client buttons only for clients
            if (user.role === 'client') {
                document.getElementById('clientActionButtons').style.display = 'flex';
                document.getElementById('staffActionButtons').style.display = 'none';
                
                // Setup button handlers
                setupClientButtons();
            } else {
                // Show staff buttons for admin, superadmin, employee
                document.getElementById('clientActionButtons').style.display = 'none';
                document.getElementById('staffActionButtons').style.display = 'flex';
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
            // Default to staff view if error
            document.getElementById('clientActionButtons').style.display = 'none';
            document.getElementById('staffActionButtons').style.display = 'flex';
        }
    } else {
        // Default to staff view if no user data
        document.getElementById('clientActionButtons').style.display = 'none';
        document.getElementById('staffActionButtons').style.display = 'flex';
    }
}

function setupClientButtons() {
    const confirmBtn = document.getElementById('confirmOrderBtn');
    const paymentBtn = document.getElementById('makePaymentBtn');
    
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            // TODO: Implement confirm order functionality
            showAlert('Confirm order functionality will be implemented soon', 'info');
        });
    }
    
    if (paymentBtn) {
        paymentBtn.addEventListener('click', function() {
            // TODO: Implement payment functionality
            showAlert('Payment functionality will be implemented soon', 'info');
        });
    }
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
            }, 5000);
        }
    }
}

function showError(message) {
    showAlert(message, 'error');
}
