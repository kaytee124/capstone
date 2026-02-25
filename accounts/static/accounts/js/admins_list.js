// Admins list functionality
let currentPage = 1;
let pageSize = 20;
let searchTerm = '';
let statusFilter = '';

document.addEventListener('DOMContentLoaded', function() {
    loadAdmins();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', function() {
        searchTerm = document.getElementById('searchInput').value;
        statusFilter = document.getElementById('statusFilter').value;
        currentPage = 1;
        loadAdmins();
    });
    
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });
}

async function loadAdmins() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        
        if (searchTerm) params.append('search', searchTerm);
        if (statusFilter) params.append('is_active', statusFilter);
        
        const response = await fetch(`/api/accounts/admins/?${params}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load admins');
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
        
        renderAdmins(data.results || []);
        renderPagination(data);
    } catch (error) {
        console.error('Error loading admins:', error);
        document.getElementById('adminsTableBody').innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 2rem; color: #ef4444;">
                    Failed to load admins. Please try again.
                </td>
            </tr>
        `;
    }
}

function renderAdmins(admins) {
    const tbody = document.getElementById('adminsTableBody');
    
    if (admins.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 2rem;">No admins found</td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = admins.map(admin => {
        // Ensure admin has an ID before creating the link
        if (!admin.id) {
            return `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 1rem; color: #ef4444;">
                        Invalid admin data
                    </td>
                </tr>
            `;
        }
        return `
            <tr>
                <td>${admin.first_name || ''} ${admin.last_name || ''}</td>
                <td>${admin.email || '-'}</td>
                <td>
                    <span class="status-badge ${admin.status}">${admin.status || 'inactive'}</span>
                </td>
                <td>
                    <a href="/api/accounts/superadmin/user/${admin.id}/" class="btn btn-sm btn-secondary">View</a>
                </td>
            </tr>
        `;
    }).join('');
}

function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    const info = pagination.querySelector('.pagination-info');
    const controls = pagination.querySelector('.pagination-controls');
    
    info.textContent = `Showing ${((data.page - 1) * data.page_size) + 1} to ${Math.min(data.page * data.page_size, data.count)} of ${data.count} admins`;
    
    controls.innerHTML = `
        <button class="pagination-btn" ${data.page === 1 ? 'disabled' : ''} onclick="goToPage(${data.page - 1})">Previous</button>
        <span>Page ${data.page} of ${data.total_pages || 1}</span>
        <button class="pagination-btn" ${data.page >= data.total_pages ? 'disabled' : ''} onclick="goToPage(${data.page + 1})">Next</button>
    `;
}

function goToPage(page) {
    currentPage = page;
    loadAdmins();
}
