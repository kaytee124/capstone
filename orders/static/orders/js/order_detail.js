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
        // Sync tokens to cookies before making API call
        if (typeof TokenManager !== 'undefined') {
            const accessToken = TokenManager.getAccessToken();
            const refreshToken = TokenManager.getRefreshToken();
            if (accessToken) {
                TokenManager.setCookie('access_token', accessToken, 3600);
            }
            if (refreshToken) {
                TokenManager.setCookie('refresh_token', refreshToken, 86400);
            }
        }
        
        // Get token for Authorization header
        const accessToken = typeof TokenManager !== 'undefined' 
            ? TokenManager.getAccessToken() 
            : localStorage.getItem('access_token');
        const refreshToken = typeof TokenManager !== 'undefined'
            ? TokenManager.getRefreshToken()
            : localStorage.getItem('refresh_token');
        
        const headers = {
            'Accept': 'application/json'
        };
        
        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }
        if (refreshToken) {
            headers['X-Refresh-Token'] = refreshToken;
        }
        
        const response = await fetch(`/api/orders/${orderId}/`, {
            method: 'GET',
            headers: headers,
            credentials: 'include'  // Include cookies in request
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
    
    const totalAmount = parseFloat(order.total_amount || 0);
    const amountPaid = parseFloat(order.amount_paid || 0);
    const remainingAmount = totalAmount - amountPaid;
    
    document.getElementById('totalAmount').textContent = `GHS ${totalAmount.toFixed(2)}`;
    document.getElementById('amountPaid').textContent = `GHS ${amountPaid.toFixed(2)}`;
    document.getElementById('remainingAmount').textContent = `GHS ${remainingAmount.toFixed(2)}`;
    
    // Update remaining amount color based on value
    const remainingAmountEl = document.getElementById('remainingAmount');
    if (remainingAmount <= 0) {
        remainingAmountEl.style.color = '#22c55e'; // Green when fully paid
        remainingAmountEl.textContent = 'GHS 0.00 (Fully Paid)';
    } else {
        remainingAmountEl.style.color = '#dc3545'; // Red when amount is due
    }
    
    document.getElementById('discountAmount').textContent = `GHS ${parseFloat(order.discount_amount || 0).toFixed(2)}`;
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
    
    // Update payment button state based on remaining amount
    updatePaymentButtonState(order);
}

function updatePaymentButtonState(order) {
    const paymentBtn = document.getElementById('makePaymentBtn');
    const paymentAmountInput = document.getElementById('paymentAmount');
    if (!paymentBtn || !paymentAmountInput) return;
    
    const totalAmount = parseFloat(order.total_amount || 0);
    const amountPaid = parseFloat(order.amount_paid || 0);
    const remainingAmount = totalAmount - amountPaid;
    
    // Set max value for payment amount input
    paymentAmountInput.max = remainingAmount;
    paymentAmountInput.placeholder = `Max: GHS ${remainingAmount.toFixed(2)}`;
    
    // Disable button if order is fully paid or no amount remaining
    if (remainingAmount <= 0 || order.payment_status === 'paid') {
        paymentBtn.disabled = true;
        paymentBtn.textContent = 'Fully Paid';
        paymentBtn.style.opacity = '0.6';
        paymentBtn.style.cursor = 'not-allowed';
        paymentAmountInput.disabled = true;
        paymentAmountInput.value = '';
    } else {
        paymentBtn.disabled = false;
        paymentBtn.textContent = 'Make Payment';
        paymentBtn.style.opacity = '1';
        paymentBtn.style.cursor = 'pointer';
        paymentAmountInput.disabled = false;
        // Set default value to remaining amount
        if (!paymentAmountInput.value) {
            paymentAmountInput.value = remainingAmount.toFixed(2);
        }
    }
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
                <td>GHS ${parseFloat(item.unit_price || 0).toFixed(2)}</td>
                <td>GHS ${subtotal.toFixed(2)}</td>
                <td title="${item.notes || ''}">${item.notes || '-'}</td>
            `;
            itemsTableBody.appendChild(row);
        });
        
        // Show footer with total
        if (itemsTableFooter) {
            const totalCell = document.getElementById('orderItemsTotal');
            if (totalCell) {
                totalCell.textContent = `GHS ${totalAmount.toFixed(2)}`;
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
        paymentBtn.addEventListener('click', async function() {
            await handleMakePayment();
        });
    }
}

async function handleMakePayment() {
    try {
        const urlParts = window.location.pathname.split('/').filter(p => p);
        const orderId = urlParts[urlParts.length - 1];
        
        if (!orderId) {
            showError('Order ID not found');
            return;
        }

        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            showError('Authentication required. Please log in again.');
            window.location.href = '/api/accounts/login/';
            return;
        }

        // Get payment amount from input field
        const paymentAmountInput = document.getElementById('paymentAmount');
        const paymentAmount = paymentAmountInput ? parseFloat(paymentAmountInput.value) : null;
        
        if (!paymentAmount || paymentAmount <= 0) {
            showError('Please enter a valid payment amount');
            paymentAmountInput?.focus();
            return;
        }

        // Get order data to validate amount
        const orderResponse = await fetch(`/api/orders/${orderId}/`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (!orderResponse.ok) {
            throw new Error('Failed to fetch order details');
        }
        
        const orderData = await orderResponse.json();
        const order = orderData.data;
        const totalAmount = parseFloat(order.total_amount || 0);
        const amountPaid = parseFloat(order.amount_paid || 0);
        const remainingAmount = totalAmount - amountPaid;
        
        if (paymentAmount > remainingAmount) {
            showError(`Payment amount (GHS ${paymentAmount.toFixed(2)}) cannot exceed remaining balance (GHS ${remainingAmount.toFixed(2)})`);
            paymentAmountInput?.focus();
            return;
        }

        // Disable button to prevent multiple clicks
        const paymentBtn = document.getElementById('makePaymentBtn');
        if (paymentBtn) {
            paymentBtn.disabled = true;
            paymentBtn.textContent = 'Processing...';
        }

        // Initialize payment
        const response = await fetch('/api/payments/initialize/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                order_id: parseInt(orderId),
                amount: paymentAmount
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to initialize payment');
        }

        if (data.status === 'success' && data.data && data.data.authorization_url) {
            // Redirect to Paystack checkout
            window.location.href = data.data.authorization_url;
        } else {
            throw new Error('Invalid response from payment server');
        }

    } catch (error) {
        console.error('Payment error:', error);
        showError(error.message || 'Failed to initialize payment. Please try again.');
        
        // Re-enable button
        const paymentBtn = document.getElementById('makePaymentBtn');
        if (paymentBtn) {
            paymentBtn.disabled = false;
            paymentBtn.textContent = 'Make Payment';
        }
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
