// Generic create user form handler (for superadmin, admin, employee)
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createForm');
    if (!form) return;
    
    const endpoint = form.getAttribute('data-endpoint') || '/api/accounts/user/create/';
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value
        };
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('User created successfully!', 'success');
                setTimeout(() => {
                    // Redirect based on role
                    if (endpoint.includes('superadmin')) {
                        window.location.href = '/api/accounts/admins/';
                    } else if (endpoint.includes('admin')) {
                        window.location.href = '/api/accounts/admins/';
                    } else if (endpoint.includes('employee')) {
                        window.location.href = '/api/accounts/employees/';
                    } else {
                        window.location.href = '/api/accounts/user/profile/';
                    }
                }, 1500);
            } else {
                showAlert(data.message || 'Failed to create user', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        } catch (error) {
            console.error('Error creating user:', error);
            showAlert('An error occurred. Please try again.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
            <span>${message}</span>
        </div>
    `;
    alertContainer.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            alertContainer.classList.add('hidden');
        }, 5000);
    }
}
