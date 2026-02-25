// Customer registration form handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            phone_number: document.getElementById('phone_number').value,
            whatsapp_number: document.getElementById('whatsapp_number').value,
            address: document.getElementById('address').value,
            preferred_contact_method: document.getElementById('preferred_contact_method').value
        };
        
        try {
            const response = await fetch('/api/customers/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('Registration successful! Redirecting to login...', 'success');
                setTimeout(() => {
                    window.location.href = '/api/accounts/login/';
                }, 2000);
            } else {
                showAlert(data.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Error registering:', error);
            showAlert('An error occurred. Please try again.', 'error');
        }
    });
});

function showAlert(message, type = 'error') {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            <span>${type === 'error' ? '✕' : type === 'success' ? '✓' : 'ℹ'}</span>
            <span>${message}</span>
        </div>
    `;
    alertContainer.classList.remove('hidden');
    
    setTimeout(() => {
        alertContainer.classList.add('hidden');
    }, 5000);
}
