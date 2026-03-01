// Service detail functionality
document.addEventListener('DOMContentLoaded', function() {
    const urlParts = window.location.pathname.split('/').filter(p => p);
    const serviceId = urlParts[urlParts.length - 1];
    
    if (serviceId) {
        loadServiceDetail(serviceId);
    } else {
        showError('Service ID not found in URL');
    }
});

async function loadServiceDetail(serviceId) {
    try {
        // Fetch all services (including inactive) to find the specific service
        const response = await fetch(`/api/services/list/?is_active=`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load service');
        }
        
        const data = await response.json();
        
        // Find the service by ID
        const service = data.data.results.find(s => s.id === parseInt(serviceId));
        
        if (!service) {
            showError('Service not found');
            return;
        }
        
        renderServiceDetail(service);
        
        // Set update button URLs
        const updateUrl = `/api/services/${serviceId}/update/`;
        document.getElementById('updateBtn').href = updateUrl;
        document.getElementById('updateBtn').style.display = 'inline-block';
        document.getElementById('updateBtnBottom').href = updateUrl;
        document.getElementById('updateBtnBottom').style.display = 'inline-block';
        
    } catch (error) {
        console.error('Error loading service:', error);
        showError('Failed to load service details. Please try again.');
    }
}

function renderServiceDetail(service) {
    document.getElementById('serviceName').textContent = service.name || '-';
    document.getElementById('serviceCategory').textContent = service.category || '-';
    
    const statusBadge = document.getElementById('serviceStatus');
    statusBadge.textContent = service.is_active ? 'Active' : 'Inactive';
    statusBadge.className = `status-badge ${service.is_active ? 'status-active' : 'status-inactive'}`;
    
    document.getElementById('name').textContent = service.name || '-';
    document.getElementById('category').textContent = service.category || '-';
    document.getElementById('price').textContent = `GHS ${parseFloat(service.price || 0).toFixed(2)}`;
    document.getElementById('unit').textContent = service.unit || '-';
    document.getElementById('estimatedDays').textContent = `${service.estimated_days || '-'} days`;
    document.getElementById('status').textContent = service.is_active ? 'Active' : 'Inactive';
    document.getElementById('description').textContent = service.description || 'No description';
}

function showError(message) {
    const container = document.querySelector('.profile-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-error" style="margin: 2rem;">
                <span>✕</span>
                <span>${message}</span>
            </div>
            <a href="/api/services/list/" class="btn btn-secondary">Back to Services</a>
        `;
    }
}
