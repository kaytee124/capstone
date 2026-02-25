// Services list functionality
let searchTerm = '';
let categoryFilter = '';
let statusFilter = '';

document.addEventListener('DOMContentLoaded', function() {
    loadServices();
    setupEventListeners();
    loadCategories();
});

function setupEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', function() {
        searchTerm = document.getElementById('searchInput').value;
        categoryFilter = document.getElementById('categoryFilter').value;
        statusFilter = document.getElementById('statusFilter').value;
        loadServices();
    });
    
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });
    
    document.getElementById('categoryFilter').addEventListener('change', function() {
        categoryFilter = this.value;
        loadServices();
    });
    
    document.getElementById('statusFilter').addEventListener('change', function() {
        statusFilter = this.value;
        loadServices();
    });
}

async function loadCategories() {
    try {
        const response = await fetch('/api/services/list/', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const categories = [...new Set(data.data.results.map(s => s.category).filter(c => c))];
            const categorySelect = document.getElementById('categoryFilter');
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categorySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadServices() {
    try {
        const params = new URLSearchParams();
        if (searchTerm) params.append('search', searchTerm);
        if (categoryFilter) params.append('category', categoryFilter);
        // Only append is_active if statusFilter is not empty (empty means all status)
        if (statusFilter) {
            params.append('is_active', statusFilter);
        }
        
        const response = await fetch(`/api/services/list/?${params}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load services');
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
        
        renderServices(data.data.results || []);
    } catch (error) {
        console.error('Error loading services:', error);
        document.getElementById('servicesTableBody').innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: #ef4444;">
                    Failed to load services. Please try again.
                </td>
            </tr>
        `;
    }
}

function renderServices(services) {
    const tbody = document.getElementById('servicesTableBody');
    
    if (services.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem;">No services found</td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = services.map(service => {
        return `
            <tr>
                <td>${service.name || '-'}</td>
                <td>${service.category || '-'}</td>
                <td>₦${parseFloat(service.price || 0).toFixed(2)}</td>
                <td>${service.unit || '-'}</td>
                <td>${service.estimated_days || '-'} days</td>
                <td>
                    <span class="status-badge ${service.is_active ? 'status-active' : 'status-inactive'}">
                        ${service.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <a href="/api/services/${service.id}/" class="btn btn-sm btn-secondary">View</a>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}
