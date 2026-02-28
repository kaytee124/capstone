// Order create functionality
let orderItems = [];
let itemCounter = 0;

document.addEventListener('DOMContentLoaded', async function() {
    loadCustomers();
    checkUserRoleAndSetupAssignTo();
    setupForm();
    // Load services first, then add the first item
    await loadServices();
    addOrderItem(); // Add first item by default after services are loaded
});

async function loadCustomers() {
    try {
        const response = await fetch('/api/accounts/clients/?page_size=1000', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Failed to load customers:', errorData);
            const customerSelect = document.getElementById('customer_id');
            if (customerSelect) {
                customerSelect.innerHTML = '<option value="">Error loading customers</option>';
            }
            return;
        }
        
        const data = await response.json();
        const customerSelect = document.getElementById('customer_id');
        
        if (!customerSelect) {
            console.error('Customer select element not found');
            return;
        }
        
        customerSelect.innerHTML = '<option value="">Select Customer</option>';
        
        if (!data.results || data.results.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No customers available';
            option.disabled = true;
            customerSelect.appendChild(option);
            console.warn('No customers found in response');
            return;
        }
        
        let customersAdded = 0;
        data.results.forEach(client => {
            // Check if client has customer profile
            if (client.customer && client.customer.id) {
                const option = document.createElement('option');
                const customerId = client.customer.id;
                // Ensure customer ID is a valid number
                if (customerId && !isNaN(customerId) && customerId > 0) {
                    option.value = String(customerId);
                    const name = `${client.first_name || ''} ${client.last_name || ''}`.trim() || client.username || 'Unknown';
                    option.textContent = `${name} (${client.username || 'N/A'})`;
                    customerSelect.appendChild(option);
                    customersAdded++;
                } else {
                    console.warn('Invalid customer ID:', customerId, 'for client:', client);
                }
            } else {
                console.warn('Client missing customer profile:', client);
            }
        });
        
        if (customersAdded === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No customers with profiles found';
            option.disabled = true;
            customerSelect.appendChild(option);
            console.warn('No customers with profiles found');
        } else {
            console.log(`Loaded ${customersAdded} customers`);
        }
    } catch (error) {
        console.error('Error loading customers:', error);
        const customerSelect = document.getElementById('customer_id');
        if (customerSelect) {
            customerSelect.innerHTML = '<option value="">Error loading customers</option>';
        }
    }
}

async function loadServices() {
    try {
        const response = await fetch('/api/services/list/?is_active=true', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            window.servicesList = data.data?.results || data.results || [];
            console.log(`Loaded ${window.servicesList.length} services`);
        } else {
            console.error('Failed to load services:', response.status);
            window.servicesList = [];
        }
    } catch (error) {
        console.error('Error loading services:', error);
        window.servicesList = [];
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
        const userId = user.id;
        
        const assignedToGroup = document.getElementById('assignedToGroup');
        const assignedSelect = document.getElementById('assigned_to');
        
        if (!assignedToGroup || !assignedSelect) {
            console.error('Assign to elements not found');
            return;
        }
        
        // For employees: hide the field and auto-set assigned_to to the employee
        if (userRole === 'employee') {
            assignedToGroup.style.display = 'none';
            // Set a hidden value or store it for form submission
            assignedSelect.value = userId;
            // Store in a data attribute for later use
            assignedSelect.setAttribute('data-auto-assigned', userId);
            console.log('Employee creating order - auto-assigning to self');
            return;
        }
        
        // For admin and superadmin: show the dropdown and load staff
        if (userRole === 'admin' || userRole === 'superadmin') {
            assignedToGroup.style.display = 'block';
            await loadStaff(userId, userRole);
        } else {
            // Hide for other roles
            assignedToGroup.style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking user role:', error);
    }
}

async function loadStaff(currentUserId, currentUserRole) {
    try {
        const assignedSelect = document.getElementById('assigned_to');
        assignedSelect.innerHTML = '<option value="">Not assigned</option>';
        
        // Get current user info to add them to the list
        const userStr = localStorage.getItem('user');
        let currentUser = null;
        if (userStr) {
            currentUser = JSON.parse(userStr);
        }
        
        // Load employees (all roles can see employees)
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
        
        // Add employees
        if (employeesRes.ok) {
            const employeesData = await employeesRes.json();
            employeesData.results.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                const isCurrentUser = currentUser && emp.id === currentUser.id;
                const label = `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || emp.username || 'Unknown';
                option.textContent = `${label} (Employee)${isCurrentUser ? ' - You' : ''}`;
                if (isCurrentUser) {
                    option.selected = true; // Pre-select current user
                }
                assignedSelect.appendChild(option);
            });
        }
        
        // Only fetch admins if user is superadmin (admins don't have permission to view admins list)
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
            
            // Add admins (only for superadmin)
            if (adminsRes.ok) {
                const adminsData = await adminsRes.json();
                adminsData.results.forEach(admin => {
                    const option = document.createElement('option');
                    option.value = admin.id;
                    const isCurrentUser = currentUser && admin.id === currentUser.id;
                    const label = `${admin.first_name || ''} ${admin.last_name || ''}`.trim() || admin.username || 'Unknown';
                    option.textContent = `${label} (Admin)${isCurrentUser ? ' - You' : ''}`;
                    if (isCurrentUser && !assignedSelect.value) {
                        option.selected = true; // Pre-select current user if nothing else is selected
                    }
                    assignedSelect.appendChild(option);
                });
            }
        }
        
        // If current user is admin, add them to the list (they can assign to themselves)
        if (currentUser && currentUserRole === 'admin') {
            const existingOption = Array.from(assignedSelect.options).find(opt => opt.value == currentUser.id);
            if (!existingOption) {
                const option = document.createElement('option');
                option.value = currentUser.id;
                const label = `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username || 'Unknown';
                option.textContent = `${label} (Admin) - You`;
                option.selected = true;
                // Insert after "Not assigned" option
                assignedSelect.insertBefore(option, assignedSelect.firstChild.nextSibling);
            } else {
                // If admin is already in the list (as employee), update the label and pre-select
                existingOption.textContent = existingOption.textContent.replace(/ \(Employee\)/, ' (Admin) - You');
                if (!assignedSelect.value) {
                    existingOption.selected = true;
                }
            }
        }
        
        // If current user is superadmin and not in the list yet, add them
        if (currentUser && currentUserRole === 'superadmin') {
            const existingOption = Array.from(assignedSelect.options).find(opt => opt.value == currentUser.id);
            if (!existingOption) {
                const option = document.createElement('option');
                option.value = currentUser.id;
                const label = `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username || 'Unknown';
                option.textContent = `${label} (Superadmin) - You`;
                option.selected = true;
                // Insert after "Not assigned" option
                assignedSelect.insertBefore(option, assignedSelect.firstChild.nextSibling);
            } else {
                // If superadmin is already in the list, make sure it's marked as "You" and pre-selected
                existingOption.textContent = existingOption.textContent.replace(/ \((Admin|Employee)\)$/, ' (Superadmin) - You');
                if (!assignedSelect.value) {
                    existingOption.selected = true;
                }
            }
        }
    } catch (error) {
        console.error('Error loading staff:', error);
    }
}

function setupForm() {
    const form = document.getElementById('createOrderForm');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
    
    const addItemBtn = document.getElementById('addItemBtn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', addOrderItem);
    }
    
    // Update totals when discount changes
    const discountInput = document.getElementById('discount_amount');
    if (discountInput) {
        discountInput.addEventListener('input', calculateTotals);
    }
}

function addOrderItem() {
    itemCounter++;
    const container = document.getElementById('orderItemsContainer');
    const itemId = `item-${itemCounter}`;
    
    const itemHtml = `
        <div class="order-item" data-item-id="${itemId}">
            <div class="order-item-header">
                <h4>Item #${itemCounter}</h4>
                <button type="button" class="remove-item-btn" onclick="removeOrderItem('${itemId}')">Remove</button>
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>Service <span class="required">*</span></label>
                    <select class="form-input service-select" data-item="${itemId}" required>
                        <option value="">Select Service</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Item Name</label>
                    <input type="text" class="form-input item-name" data-item="${itemId}" placeholder="Auto-filled from service">
                </div>
                <div class="form-group">
                    <label>Quantity <span class="required">*</span></label>
                    <input type="number" class="form-input item-quantity" data-item="${itemId}" min="1" value="1" required>
                </div>
                <div class="form-group">
                    <label>Unit Price <span class="required">*</span></label>
                    <input type="number" class="form-input item-unit-price" data-item="${itemId}" step="0.01" min="0" required>
                </div>
                <div class="form-group">
                    <label>Subtotal</label>
                    <input type="text" class="form-input item-subtotal" data-item="${itemId}" readonly>
                </div>
                <div class="form-group full-width">
                    <label>Description</label>
                    <textarea class="form-input item-description" data-item="${itemId}" rows="2"></textarea>
                </div>
                <div class="form-group full-width">
                    <label>Notes</label>
                    <textarea class="form-input item-notes" data-item="${itemId}" rows="2"></textarea>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', itemHtml);
    
    // Populate service dropdown
    const serviceSelect = container.querySelector(`[data-item="${itemId}"].service-select`);
    if (serviceSelect) {
        if (window.servicesList && window.servicesList.length > 0) {
            window.servicesList.forEach(service => {
                const option = document.createElement('option');
                option.value = service.id;
                option.textContent = `${service.name} - ₦${parseFloat(service.price).toFixed(2)}/${service.unit || 'item'}`;
                option.dataset.price = service.price;
                option.dataset.name = service.name;
                option.dataset.description = service.description || '';
                serviceSelect.appendChild(option);
            });
        } else {
            // Services not loaded yet, try loading them
            console.log('Services not loaded, loading now...');
            loadServices().then(() => {
                // Re-populate this dropdown after services are loaded
                if (window.servicesList && window.servicesList.length > 0) {
                    window.servicesList.forEach(service => {
                        const option = document.createElement('option');
                        option.value = service.id;
                        option.textContent = `${service.name} - ₦${parseFloat(service.price).toFixed(2)}/${service.unit || 'item'}`;
                        option.dataset.price = service.price;
                        option.dataset.name = service.name;
                        option.dataset.description = service.description || '';
                        serviceSelect.appendChild(option);
                    });
                }
            });
        }
    }
    
    // Setup event listeners for this item
    setupItemListeners(itemId);
    calculateTotals();
}

function setupItemListeners(itemId) {
    const serviceSelect = document.querySelector(`[data-item="${itemId}"].service-select`);
    const quantityInput = document.querySelector(`[data-item="${itemId}"].item-quantity`);
    const unitPriceInput = document.querySelector(`[data-item="${itemId}"].item-unit-price`);
    const itemNameInput = document.querySelector(`[data-item="${itemId}"].item-name`);
    const descriptionInput = document.querySelector(`[data-item="${itemId}"].item-description`);
    
    if (serviceSelect) {
        serviceSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption && selectedOption.value) {
                const price = parseFloat(selectedOption.dataset.price || 0);
                const name = selectedOption.dataset.name || '';
                const description = selectedOption.dataset.description || '';
                
                if (unitPriceInput) unitPriceInput.value = price.toFixed(2);
                if (itemNameInput) itemNameInput.value = name;
                if (descriptionInput) descriptionInput.value = description;
                
                calculateItemSubtotal(itemId);
                calculateTotals();
            }
        });
    }
    
    if (quantityInput) {
        quantityInput.addEventListener('input', function() {
            calculateItemSubtotal(itemId);
            calculateTotals();
        });
    }
    
    if (unitPriceInput) {
        unitPriceInput.addEventListener('input', function() {
            calculateItemSubtotal(itemId);
            calculateTotals();
        });
    }
}

function calculateItemSubtotal(itemId) {
    const quantityInput = document.querySelector(`[data-item="${itemId}"].item-quantity`);
    const unitPriceInput = document.querySelector(`[data-item="${itemId}"].item-unit-price`);
    const subtotalInput = document.querySelector(`[data-item="${itemId}"].item-subtotal`);
    
    if (quantityInput && unitPriceInput && subtotalInput) {
        const quantity = parseFloat(quantityInput.value) || 0;
        const unitPrice = parseFloat(unitPriceInput.value) || 0;
        const subtotal = quantity * unitPrice;
        subtotalInput.value = `₦${subtotal.toFixed(2)}`;
    }
}

function calculateTotals() {
    let subtotal = 0;
    
    document.querySelectorAll('.order-item').forEach(item => {
        const itemId = item.dataset.itemId;
        const quantityInput = item.querySelector(`[data-item="${itemId}"].item-quantity`);
        const unitPriceInput = item.querySelector(`[data-item="${itemId}"].item-unit-price`);
        
        if (quantityInput && unitPriceInput) {
            const quantity = parseFloat(quantityInput.value) || 0;
            const unitPrice = parseFloat(unitPriceInput.value) || 0;
            subtotal += quantity * unitPrice;
        }
    });
    
    const discount = parseFloat(document.getElementById('discount_amount').value) || 0;
    const total = subtotal - discount;
    
    document.getElementById('subtotal').textContent = `₦${subtotal.toFixed(2)}`;
    document.getElementById('discount').textContent = `₦${discount.toFixed(2)}`;
    document.getElementById('totalAmount').textContent = `₦${total.toFixed(2)}`;
}

function removeOrderItem(itemId) {
    const item = document.querySelector(`[data-item-id="${itemId}"]`);
    if (item) {
        item.remove();
        calculateTotals();
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';
    
    try {
        // Collect order items
        const orderItemsData = [];
        document.querySelectorAll('.order-item').forEach(item => {
            const itemId = item.dataset.itemId;
            const serviceSelect = item.querySelector(`[data-item="${itemId}"].service-select`);
            const quantityInput = item.querySelector(`[data-item="${itemId}"].item-quantity`);
            const unitPriceInput = item.querySelector(`[data-item="${itemId}"].item-unit-price`);
            const itemNameInput = item.querySelector(`[data-item="${itemId}"].item-name`);
            const descriptionInput = item.querySelector(`[data-item="${itemId}"].item-description`);
            const notesInput = item.querySelector(`[data-item="${itemId}"].item-notes`);
            
            if (serviceSelect && serviceSelect.value && quantityInput && unitPriceInput) {
                orderItemsData.push({
                    service_id: parseInt(serviceSelect.value),
                    item_name: itemNameInput ? itemNameInput.value.trim() : '',
                    description: descriptionInput ? descriptionInput.value.trim() : '',
                    quantity: parseInt(quantityInput.value) || 1,
                    unit_price: parseFloat(unitPriceInput.value) || 0,
                    notes: notesInput ? notesInput.value.trim() : ''
                });
            }
        });
        
        if (orderItemsData.length === 0) {
            showAlert('Please add at least one order item', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        // Get assigned_to value - check if it was auto-assigned for employees
        const assignedSelect = document.getElementById('assigned_to');
        let assignedToValue = null;
        if (assignedSelect) {
            const autoAssigned = assignedSelect.getAttribute('data-auto-assigned');
            if (autoAssigned) {
                // Employee creating order - use auto-assigned value
                assignedToValue = parseInt(autoAssigned);
            } else if (assignedSelect.value) {
                // Admin/superadmin selected someone
                assignedToValue = parseInt(assignedSelect.value);
            }
        }
        
        // Validate customer selection
        const customerSelect = document.getElementById('customer_id');
        if (!customerSelect) {
            showAlert('Customer field not found', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        const customerIdValue = customerSelect.value;
        console.log('Customer ID value:', customerIdValue, 'Type:', typeof customerIdValue);
        
        if (!customerIdValue || customerIdValue === '' || customerIdValue === '0') {
            showAlert('Please select a customer', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        const customerId = parseInt(customerIdValue, 10);
        console.log('Parsed customer ID:', customerId);
        
        if (isNaN(customerId) || customerId <= 0) {
            showAlert('Invalid customer selected. Please select a valid customer.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        // Collect form data
        // Note: order_status, payment_status, and amount_paid are set by the backend with defaults
        const formData = {
            customer_id: customerId,
            assigned_to: assignedToValue,
            discount_amount: parseFloat(document.getElementById('discount_amount').value) || 0,
            pickup_date: document.getElementById('pickup_date').value || null,
            delivery_date: document.getElementById('delivery_date').value || null,
            estimated_completion_date: document.getElementById('estimated_completion_date').value || null,
            delivery_notes: document.getElementById('delivery_notes').value.trim(),
            special_instructions: document.getElementById('special_instructions').value.trim(),
            order_items_data: orderItemsData
        };
        
        console.log('Form data being sent:', formData);
        
        const response = await fetch('/api/orders/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        });
        
        // Check if response is JSON
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
            showAlert('Order created successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/api/orders/list/';
            }, 1500);
        } else {
            // Log the full error response for debugging
            console.error('Error response:', data);
            console.error('Response status:', response.status);
            const errorMessage = extractErrorMessage(data);
            console.error('Extracted error message:', errorMessage);
            showAlert(errorMessage, 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error creating order:', error);
        let errorMessage = 'An error occurred. Please try again.';
        
        if (error.message) {
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage = 'Network error. Please check your connection and try again.';
            } else {
                errorMessage = error.message;
            }
        }
        
        showAlert(errorMessage, 'error');
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
    
    const fieldErrors = [];
    for (const [field, errors] of Object.entries(data)) {
        if (field === 'error_code' || field === 'status_code' || field === 'message' || field === 'detail') {
            continue;
        }
        
        if (Array.isArray(errors) && errors.length > 0) {
            const errorMsg = errors[0];
            let msg = '';
            
            if (typeof errorMsg === 'string') {
                msg = errorMsg;
            } else if (errorMsg && typeof errorMsg === 'object') {
                msg = errorMsg.string || errorMsg.message || errorMsg.detail || '';
                if (!msg) {
                    const objStr = String(errorMsg);
                    const match = objStr.match(/string=['"]([^'"]+)['"]/);
                    msg = match ? match[1] : objStr;
                }
            } else {
                msg = String(errorMsg);
            }
            
            if (msg) {
                const fieldName = field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                fieldErrors.push(`${fieldName}: ${msg}`);
            }
        } else if (typeof errors === 'string') {
            const fieldName = field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            fieldErrors.push(`${fieldName}: ${errors}`);
        }
    }
    
    if (fieldErrors.length > 0) {
        return fieldErrors.join('. ');
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
