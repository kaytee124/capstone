// Clients list functionality
let currentPage = 1;
let pageSize = 20;
let searchTerm = '';
let statusFilter = '';

// Get the appropriate view URL based on current user's role
function getViewUrl(userId) {
    const userData = localStorage.getItem('user');
    if (userData) {
        try {
            const currentUser = JSON.parse(userData);
            if (currentUser.role === 'superadmin') {
                return `/api/accounts/superadmin/user/${userId}/`;
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }
    // Default to staff URL for employees and admins
    return `/api/accounts/staff/user/${userId}/`;
}

document.addEventListener('DOMContentLoaded', function() {
    loadClients();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', function() {
        searchTerm = document.getElementById('searchInput').value;
        statusFilter = document.getElementById('statusFilter').value;
        currentPage = 1;
        loadClients();
    });
    
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });
}

async function loadClients() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        
        if (searchTerm) params.append('search', searchTerm);
        if (statusFilter) params.append('is_active', statusFilter);
        
        // Use global fetch which automatically handles tokens and refresh
        const response = await fetch(`/api/accounts/clients/?${params}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            // If response is not ok, the global fetch interceptor should handle redirect
            // But if we get here, show error
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || 'Failed to load clients');
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
        
        renderClients(data.results || []);
        renderPagination(data);
    } catch (error) {
        console.error('Error loading clients:', error);
        const tbody = document.getElementById('clientsTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 2rem; color: #ef4444;">
                        Failed to load clients. Please try again.
                    </td>
                </tr>
            `;
        }
    }
}

function renderClients(clients) {
    const tbody = document.getElementById('clientsTableBody');
    
    if (clients.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem;">No clients found</td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = clients.map(client => {
        // Ensure client has an ID before creating the link
        if (!client.id) {
            return `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 1rem; color: #ef4444;">
                        Invalid client data
                    </td>
                </tr>
            `;
        }
        return `
            <tr>
                <td>${client.first_name || ''} ${client.last_name || ''}</td>
                <td>${client.email || '-'}</td>
                <td>${client.phone_number || '-'}</td>
                <td>
                    <span class="status-badge ${client.status}">${client.status || 'inactive'}</span>
                </td>
                <td>${client.total_orders || 0}</td>
                <td>$${client.total_spent || '0.00'}</td>
                <td>
                    <a href="${getViewUrl(client.id)}" class="btn btn-sm btn-secondary">View</a>
                </td>
            </tr>
        `;
    }).join('');
}

function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    const info = pagination.querySelector('.pagination-info');
    const controls = pagination.querySelector('.pagination-controls');
    
    info.textContent = `Showing ${((data.page - 1) * data.page_size) + 1} to ${Math.min(data.page * data.page_size, data.count)} of ${data.count} clients`;
    
    controls.innerHTML = `
        <button class="pagination-btn" ${data.page === 1 ? 'disabled' : ''} onclick="goToPage(${data.page - 1})">Previous</button>
        <span>Page ${data.page} of ${data.total_pages || 1}</span>
        <button class="pagination-btn" ${data.page >= data.total_pages ? 'disabled' : ''} onclick="goToPage(${data.page + 1})">Next</button>
    `;
}

function goToPage(page) {
    currentPage = page;
    loadClients();
}
