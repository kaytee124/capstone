// Function to update username display in header (can be called from other scripts)
// Make it globally accessible
window.updateUserNameDisplay = function() {
    const userName = document.getElementById('userName');
    if (!userName) return;
    
    const userData = localStorage.getItem('user');
    if (userData) {
        try {
            const user = JSON.parse(userData);
            userName.textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
        } catch (e) {
            userName.textContent = 'User';
        }
    } else {
        userName.textContent = 'User';
    }
};

// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    // Load user info on page load
    if (typeof window.updateUserNameDisplay === 'function') {
        window.updateUserNameDisplay();
    }

    // Show/hide sections based on user role
    const userData = localStorage.getItem('user');
    const userRole = userData ? JSON.parse(userData).role : null;
    
    // Orders section visible to all authenticated users
    if (userRole) {
        const ordersSection = document.getElementById('ordersSection');
        if (ordersSection) {
            ordersSection.style.display = 'block';
            
            // Show "Create Order" link only for admin, superadmin, and employee
            if (['admin', 'superadmin', 'employee'].includes(userRole)) {
                const createOrderLink = document.getElementById('createOrderLink');
                if (createOrderLink) createOrderLink.style.display = 'block';
            }
            
            // Ensure orders links work with authentication
            // Since tokens are stored in cookies by the login view, regular href navigation will work
            // But we can also intercept clicks to ensure tokens are available
            const ordersListLink = document.getElementById('ordersListLink');
            if (ordersListLink) {
                ordersListLink.addEventListener('click', function(e) {
                    // Check if token exists, if not, redirect to login
                    const accessToken = typeof TokenManager !== 'undefined' 
                        ? TokenManager.getAccessToken() 
                        : localStorage.getItem('access_token');
                    
                    if (!accessToken) {
                        e.preventDefault();
                        window.location.href = '/api/accounts/login/?next=' + encodeURIComponent(this.href);
                    }
                    // Otherwise, let the link work normally (cookies will handle auth)
                });
            }
            
            const createOrderLink = document.getElementById('createOrderLink');
            if (createOrderLink) {
                const linkElement = createOrderLink.querySelector('a');
                if (linkElement) {
                    linkElement.addEventListener('click', function(e) {
                        const accessToken = typeof TokenManager !== 'undefined' 
                            ? TokenManager.getAccessToken() 
                            : localStorage.getItem('access_token');
                        
                        if (!accessToken) {
                            e.preventDefault();
                            window.location.href = '/api/accounts/login/?next=' + encodeURIComponent(this.href);
                        }
                    });
                }
            }
        }
    }
    
    if (userRole === 'client') {
        const clientSection = document.getElementById('clientSection');
        if (clientSection) clientSection.style.display = 'block';
    }
    
    if (userRole === 'employee') {
        const employeeSection = document.getElementById('employeeSection');
        if (employeeSection) employeeSection.style.display = 'block';
    }
    
    // Clients section visible to staff (employees, admins, superadmins)
    if (['employee', 'admin', 'superadmin'].includes(userRole)) {
        const clientsSection = document.getElementById('clientsSection');
        if (clientsSection) clientsSection.style.display = 'block';
    }
    
    // Staff section (for staff management - can be expanded later)
    if (['employee', 'admin', 'superadmin'].includes(userRole)) {
        const staffSection = document.getElementById('staffSection');
        if (staffSection) staffSection.style.display = 'block';
    }
    
    if (userRole === 'admin' || userRole === 'superadmin') {
        const adminSection = document.getElementById('adminSection');
        if (adminSection) adminSection.style.display = 'block';
    }
    
    if (userRole === 'superadmin') {
        const superadminSection = document.getElementById('superadminSection');
        if (superadminSection) superadminSection.style.display = 'block';
    }

    // Sidebar toggle for mobile
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
    
    // Handle logout link click
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const refreshToken = typeof TokenManager !== 'undefined' 
                ? TokenManager.getRefreshToken() 
                : localStorage.getItem('refresh_token') || '';
            
            if (refreshToken) {
                try {
                    // Try to blacklist the token via POST
                    await fetch('/api/accounts/logout/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            refresh: refreshToken
                        })
                    });
                } catch (error) {
                    console.error('Logout error:', error);
                }
            }
            
            // Clear tokens and redirect
            if (typeof TokenManager !== 'undefined') {
                TokenManager.clearTokens();
            } else {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
            }
            
            // Redirect to login
            window.location.href = '/api/accounts/login/';
        });
    }
});
