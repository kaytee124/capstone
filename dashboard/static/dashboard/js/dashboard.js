// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardMetrics();
});

function loadDashboardMetrics() {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!accessToken) {
        // No token, redirect to login
        window.location.href = '/api/accounts/login/?error=NO_TOKEN&message=Authentication required. Please log in to continue.';
        return;
    }
    
    fetch('/api/dashboard/metrics/', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'X-Refresh-Token': refreshToken || '',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 401) {
            // Token expired, try to refresh
            return handleTokenRefresh().then(() => loadDashboardMetrics());
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            renderDashboard(data.data);
        } else {
            // Check if it's an authentication error
            if (data.error_code === 'NO_TOKEN' || data.error_code === 'INVALID_TOKEN') {
                window.location.href = '/api/accounts/login/?error=' + data.error_code + '&message=' + encodeURIComponent(data.message || 'Authentication required. Please log in to continue.');
            } else {
                showError(data.message || 'Failed to load dashboard metrics');
            }
        }
    })
    .catch(error => {
        console.error('Dashboard error:', error);
        // On error, check if we have tokens, if not redirect to login
        const accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            window.location.href = '/api/accounts/login/?error=NO_TOKEN&message=Authentication required. Please log in to continue.';
        } else {
            showError('Failed to load dashboard metrics');
        }
    });
}

function renderDashboard(data) {
    const container = document.getElementById('dashboardContent');
    const userRole = getUserRole();
    
    let html = '';
    
    if (userRole === 'superadmin') {
        html = renderSuperadminDashboard(data);
    } else if (userRole === 'admin') {
        html = renderAdminDashboard(data);
    } else if (userRole === 'employee') {
        html = renderEmployeeDashboard(data);
    } else if (userRole === 'client') {
        html = renderClientDashboard(data);
    } else {
        html = '<div class="error">Invalid user role</div>';
    }
    
    container.innerHTML = html;
}

function renderSuperadminDashboard(data) {
    let html = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Customers</span>
                    <div class="metric-icon" style="background: #e3f2fd; color: #1976d2;">
                        👥
                    </div>
                </div>
                <div class="metric-value">${data.total_customers || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Staff</span>
                    <div class="metric-icon" style="background: #f3e5f5; color: #7b1fa2;">
                        👔
                    </div>
                </div>
                <div class="metric-value">${data.total_staff || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Orders</span>
                    <div class="metric-icon" style="background: #e8f5e9; color: #388e3c;">
                        📦
                    </div>
                </div>
                <div class="metric-value">${data.total_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Revenue</span>
                    <div class="metric-icon" style="background: #fff3e0; color: #f57c00;">
                        💰
                    </div>
                </div>
                <div class="metric-value currency">GHS ${formatCurrency(data.total_revenue || 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Today's Orders</span>
                    <div class="metric-icon" style="background: #e1f5fe; color: #0277bd;">
                        📅
                    </div>
                </div>
                <div class="metric-value">${data.today_orders || 0}</div>
                <div class="metric-subtitle">GHS ${formatCurrency(data.today_revenue || 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Pending Orders</span>
                    <div class="metric-icon" style="background: #fff3cd; color: #856404;">
                        ⏳
                    </div>
                </div>
                <div class="metric-value">${data.pending_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">In Progress</span>
                    <div class="metric-icon" style="background: #d1ecf1; color: #0c5460;">
                        🔄
                    </div>
                </div>
                <div class="metric-value">${data.in_progress_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Ready for Pickup</span>
                    <div class="metric-icon" style="background: #d4edda; color: #155724;">
                        ✅
                    </div>
                </div>
                <div class="metric-value">${data.ready_for_pickup || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Outstanding</span>
                    <div class="metric-icon" style="background: #f8d7da; color: #721c24;">
                        ⚠️
                    </div>
                </div>
                <div class="metric-value currency">GHS ${formatCurrency(data.total_outstanding || 0)}</div>
            </div>
        </div>
    `;
    
    if (data.recent_orders && data.recent_orders.length > 0) {
        html += `
            <div class="recent-orders-section">
                <h2 class="section-title">Recent Orders</h2>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Order Number</th>
                            <th>Customer</th>
                            <th>Total Amount</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.recent_orders.forEach(order => {
            html += `
                <tr>
                    <td>${order.order_number || 'N/A'}</td>
                    <td>${order.customer_name || 'N/A'}</td>
                    <td class="currency">GHS ${formatCurrency(order.total_amount || 0)}</td>
                    <td><span class="status-badge status-${order.status}">${order.status}</span></td>
                    <td><a href="/api/orders/${order.id}/" class="btn btn-sm">View</a></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<div class="recent-orders-section"><div class="no-data">No recent orders</div></div>';
    }
    
    return html;
}

function renderAdminDashboard(data) {
    let html = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Customers</span>
                    <div class="metric-icon" style="background: #e3f2fd; color: #1976d2;">
                        👥
                    </div>
                </div>
                <div class="metric-value">${data.total_customers || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Orders</span>
                    <div class="metric-icon" style="background: #e8f5e9; color: #388e3c;">
                        📦
                    </div>
                </div>
                <div class="metric-value">${data.total_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Revenue</span>
                    <div class="metric-icon" style="background: #fff3e0; color: #f57c00;">
                        💰
                    </div>
                </div>
                <div class="metric-value currency">GHS ${formatCurrency(data.total_revenue || 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Today's Orders</span>
                    <div class="metric-icon" style="background: #e1f5fe; color: #0277bd;">
                        📅
                    </div>
                </div>
                <div class="metric-value">${data.today_orders || 0}</div>
                <div class="metric-subtitle">GHS ${formatCurrency(data.today_revenue || 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Pending Orders</span>
                    <div class="metric-icon" style="background: #fff3cd; color: #856404;">
                        ⏳
                    </div>
                </div>
                <div class="metric-value">${data.pending_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Ready for Pickup</span>
                    <div class="metric-icon" style="background: #d4edda; color: #155724;">
                        ✅
                    </div>
                </div>
                <div class="metric-value">${data.ready_for_pickup || 0}</div>
            </div>
        </div>
    `;
    
    if (data.recent_orders && data.recent_orders.length > 0) {
        html += `
            <div class="recent-orders-section">
                <h2 class="section-title">Recent Orders</h2>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Order Number</th>
                            <th>Customer</th>
                            <th>Total Amount</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.recent_orders.forEach(order => {
            html += `
                <tr>
                    <td>${order.order_number || 'N/A'}</td>
                    <td>${order.customer_name || 'N/A'}</td>
                    <td class="currency">GHS ${formatCurrency(order.total_amount || 0)}</td>
                    <td><span class="status-badge status-${order.status}">${order.status}</span></td>
                    <td><a href="/api/orders/${order.id}/" class="btn btn-sm">View</a></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<div class="recent-orders-section"><div class="no-data">No recent orders</div></div>';
    }
    
    return html;
}

function renderEmployeeDashboard(data) {
    let html = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">My Orders</span>
                    <div class="metric-icon" style="background: #e8f5e9; color: #388e3c;">
                        📦
                    </div>
                </div>
                <div class="metric-value">${data.my_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">My Pending</span>
                    <div class="metric-icon" style="background: #fff3cd; color: #856404;">
                        ⏳
                    </div>
                </div>
                <div class="metric-value">${data.my_pending || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">In Progress</span>
                    <div class="metric-icon" style="background: #d1ecf1; color: #0c5460;">
                        🔄
                    </div>
                </div>
                <div class="metric-value">${data.my_in_progress || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Today's Orders</span>
                    <div class="metric-icon" style="background: #e1f5fe; color: #0277bd;">
                        📅
                    </div>
                </div>
                <div class="metric-value">${data.my_today_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">My Revenue</span>
                    <div class="metric-icon" style="background: #fff3e0; color: #f57c00;">
                        💰
                    </div>
                </div>
                <div class="metric-value currency">GHS ${formatCurrency(data.my_revenue || 0)}</div>
            </div>
        </div>
    `;
    
    if (data.my_assigned_orders && data.my_assigned_orders.length > 0) {
        html += `
            <div class="recent-orders-section">
                <h2 class="section-title">My Assigned Orders</h2>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Order Number</th>
                            <th>Customer</th>
                            <th>Status</th>
                            <th>Est. Completion</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.my_assigned_orders.forEach(order => {
            const estDate = order.estimated_completion ? new Date(order.estimated_completion).toLocaleDateString() : 'N/A';
            html += `
                <tr>
                    <td>${order.order_number || 'N/A'}</td>
                    <td>${order.customer_name || 'N/A'}</td>
                    <td><span class="status-badge status-${order.status}">${order.status}</span></td>
                    <td>${estDate}</td>
                    <td><a href="/api/orders/${order.id}/" class="btn btn-sm">View</a></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<div class="recent-orders-section"><div class="no-data">No assigned orders</div></div>';
    }
    
    return html;
}

function renderClientDashboard(data) {
    let html = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Orders</span>
                    <div class="metric-icon" style="background: #e8f5e9; color: #388e3c;">
                        📦
                    </div>
                </div>
                <div class="metric-value">${data.total_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Total Spent</span>
                    <div class="metric-icon" style="background: #fff3e0; color: #f57c00;">
                        💰
                    </div>
                </div>
                <div class="metric-value currency">GHS ${formatCurrency(data.total_spent || 0)}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Pending Orders</span>
                    <div class="metric-icon" style="background: #fff3cd; color: #856404;">
                        ⏳
                    </div>
                </div>
                <div class="metric-value">${data.pending_orders || 0}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-card-header">
                    <span class="metric-title">Ready for Pickup</span>
                    <div class="metric-icon" style="background: #d4edda; color: #155724;">
                        ✅
                    </div>
                </div>
                <div class="metric-value">${data.ready_for_pickup || 0}</div>
            </div>
        </div>
    `;
    
    if (data.recent_orders && data.recent_orders.length > 0) {
        html += `
            <div class="recent-orders-section">
                <h2 class="section-title">Recent Orders</h2>
                <table class="orders-table">
                    <thead>
                        <tr>
                            <th>Order Number</th>
                            <th>Total Amount</th>
                            <th>Balance</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.recent_orders.forEach(order => {
            const createdDate = order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A';
            html += `
                <tr>
                    <td>${order.order_number || 'N/A'}</td>
                    <td class="currency">GHS ${formatCurrency(order.total_amount || 0)}</td>
                    <td class="currency">GHS ${formatCurrency(order.balance || 0)}</td>
                    <td><span class="status-badge status-${order.status}">${order.status}</span></td>
                    <td>${createdDate}</td>
                    <td><a href="/api/orders/${order.id}/" class="btn btn-sm">View</a></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<div class="recent-orders-section"><div class="no-data">No recent orders</div></div>';
    }
    
    return html;
}

function getUserRole() {
    const userData = localStorage.getItem('user');
    if (userData) {
        try {
            const user = JSON.parse(userData);
            return user.role || 'client';
        } catch (e) {
            return 'client';
        }
    }
    return 'client';
}

function formatCurrency(amount) {
    if (typeof amount === 'string') {
        amount = parseFloat(amount);
    }
    return amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function showError(message) {
    const container = document.getElementById('dashboardContent');
    container.innerHTML = `<div class="error">${message}</div>`;
}

function handleTokenRefresh() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        window.location.href = '/api/accounts/login/?error=NO_TOKEN&message=Authentication required. Please log in to continue.';
        return Promise.reject('No refresh token');
    }
    
    return fetch('/api/accounts/token/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Refresh-Token': refreshToken
        },
        body: JSON.stringify({ refresh: refreshToken })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access) {
            localStorage.setItem('access_token', data.access);
            if (data.refresh) {
                localStorage.setItem('refresh_token', data.refresh);
            }
            return Promise.resolve();
        } else {
            window.location.href = '/api/accounts/login/?error=INVALID_TOKEN&message=Session expired. Please log in again.';
            return Promise.reject('Token refresh failed');
        }
    })
    .catch(error => {
        window.location.href = '/api/accounts/login/?error=INVALID_TOKEN&message=Session expired. Please log in again.';
        return Promise.reject(error);
    });
}
