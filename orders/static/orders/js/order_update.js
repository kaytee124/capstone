// Order update functionality
document.addEventListener('DOMContentLoaded', function() {
    const urlParts = window.location.pathname.split('/').filter(p => p);
    const orderId = urlParts[urlParts.length - 2]; // Get order ID from URL (before 'update')
    
    if (orderId) {
        loadOrder(orderId);
        setupForm(orderId);
        checkUserRoleAndSetupAssignTo();
    } else {
        showError('Order ID not found in URL');
    }
});

async function loadOrder(orderId) {
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
        populateForm(data.data);
    } catch (error) {
        console.error('Error loading order:', error);
        showError('Failed to load order details. Please try again.');
    }
}

function populateForm(order) {
    document.getElementById('order_number').value = order.order_number || '';
    document.getElementById('customer_name').value = order.customer_name || order.customer_username || '';
    document.getElementById('order_status').value = order.order_status || 'pending';
    document.getElementById('payment_status').value = order.payment_status || 'pending';
    document.getElementById('total_amount').value = `₦${parseFloat(order.total_amount || 0).toFixed(2)}`;
    document.getElementById('amount_paid').value = `₦${parseFloat(order.amount_paid || 0).toFixed(2)}`;
    document.getElementById('discount_amount').value = parseFloat(order.discount_amount || 0);
    document.getElementById('pickup_date').value = order.pickup_date || '';
    document.getElementById('delivery_date').value = order.delivery_date || '';
    document.getElementById('estimated_completion_date').value = order.estimated_completion_date || '';
    document.getElementById('delivery_notes').value = order.delivery_notes || '';
    document.getElementById('special_instructions').value = order.special_instructions || '';
    
    // Set assigned_to after loading staff
    if (order.assigned_to) {
        setTimeout(() => {
            const assignedSelect = document.getElementById('assigned_to');
            if (assignedSelect) {
                assignedSelect.value = order.assigned_to;
            }
        }, 500);
    }
}

async function checkUserRoleAndSetupAssignTo() {
    try {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            console.error('User data not found');
            return;
        }
        
        const user = JSON.parse(userStr);
        const userRole = user.role;
        
        const assignedToGroup = document.getElementById('assignedToGroup');
        const assignedSelect = document.getElementById('assigned_to');
        
        if (!assignedToGroup || !assignedSelect) {
            console.error('Assign to elements not found');
            return;
        }
        
        // For employees: hide the field
        if (userRole === 'employee') {
            assignedToGroup.style.display = 'none';
        } else if (userRole === 'admin' || userRole === 'superadmin') {
            assignedToGroup.style.display = 'block';
            await loadStaff(userRole);
        } else {
            assignedToGroup.style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking user role:', error);
    }
}

async function loadStaff(currentUserRole) {
    try {
        const assignedSelect = document.getElementById('assigned_to');
        assignedSelect.innerHTML = '<option value="">Not assigned</option>';
        
        const userStr = localStorage.getItem('user');
        let currentUser = null;
        if (userStr) {
            currentUser = JSON.parse(userStr);
        }
        
        // Load employees
        let employeesRes;
        try {
            employeesRes = await fetch('/api/accounts/employees/?page_size=1000', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
        } catch (error) {
            console.error('Error fetching employees:', error);
            employeesRes = { ok: false };
        }
        
        if (employeesRes.ok) {
            const employeesData = await employeesRes.json();
            employeesData.results.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                const label = `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || emp.username || 'Unknown';
                option.textContent = `${label} (Employee)`;
                assignedSelect.appendChild(option);
            });
        }
        
        // Only fetch admins if user is superadmin
        if (currentUserRole === 'superadmin') {
            let adminsRes;
            try {
                adminsRes = await fetch('/api/accounts/admins/?page_size=1000', {
                    headers: {
                        'Accept': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });
            } catch (error) {
                console.error('Error fetching admins:', error);
                adminsRes = { ok: false };
            }
            
            if (adminsRes.ok) {
                const adminsData = await adminsRes.json();
                adminsData.results.forEach(admin => {
                    const option = document.createElement('option');
                    option.value = admin.id;
                    const label = `${admin.first_name || ''} ${admin.last_name || ''}`.trim() || admin.username || 'Unknown';
                    option.textContent = `${label} (Admin)`;
                    assignedSelect.appendChild(option);
                });
            }
        }
        
        // Add current user if admin
        if (currentUser && currentUserRole === 'admin') {
            const existingOption = Array.from(assignedSelect.options).find(opt => opt.value == currentUser.id);
            if (!existingOption) {
                const option = document.createElement('option');
                option.value = currentUser.id;
                const label = `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username || 'Unknown';
                option.textContent = `${label} (Admin)`;
                assignedSelect.insertBefore(option, assignedSelect.firstChild.nextSibling);
            }
        }
    } catch (error) {
        console.error('Error loading staff:', error);
    }
}

function setupForm(orderId) {
    const form = document.getElementById('updateOrderForm');
    if (form) {
        form.addEventListener('submit', (e) => handleSubmit(e, orderId));
    }
}

async function handleSubmit(e, orderId) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Updating...';
    
    try {
        const formData = {
            assigned_to: document.getElementById('assigned_to').value ? parseInt(document.getElementById('assigned_to').value) : null,
            order_status: document.getElementById('order_status').value,
            payment_status: document.getElementById('payment_status').value,
            discount_amount: parseFloat(document.getElementById('discount_amount').value) || 0,
            pickup_date: document.getElementById('pickup_date').value || null,
            delivery_date: document.getElementById('delivery_date').value || null,
            estimated_completion_date: document.getElementById('estimated_completion_date').value || null,
            delivery_notes: document.getElementById('delivery_notes').value.trim(),
            special_instructions: document.getElementById('special_instructions').value.trim()
        };
        
        const response = await fetch(`/api/orders/${orderId}/update/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        });
        
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            showAlert('Invalid response from server. Please try again.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        if (response.ok) {
            showAlert('Order updated successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/api/orders/list/';
            }, 1500);
        } else {
            const errorMessage = extractErrorMessage(data);
            showAlert(errorMessage, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error updating order:', error);
        showAlert('An error occurred. Please try again.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function extractErrorMessage(data) {
    if (typeof data === 'string') {
        try {
            data = JSON.parse(data);
        } catch (e) {
            return data;
        }
    }
    
    if (data.error_code) {
        return data.message || 'An error occurred';
    }
    
    if (data.message) {
        if (Array.isArray(data.message)) {
            const msg = data.message[0];
            return typeof msg === 'string' ? msg : (msg?.string || String(msg));
        }
        if (typeof data.message === 'string') {
            return data.message;
        }
    }
    
    return 'Validation failed. Please check your input.';
}

function showAlert(message, type = 'error') {
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

function showError(message) {
    showAlert(message, 'error');
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
