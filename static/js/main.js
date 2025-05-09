/**
 * Main JavaScript file for Chikitsa360
 */

// Set up CSRF token for AJAX requests
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

// Add CSRF token to AJAX requests
const csrftoken = getCookie('csrftoken');

// Set up AJAX headers
function setupAjax() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}

// Initialize tooltips and popovers
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Show notifications
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `fixed top-4 right-4 p-4 rounded-md shadow-md z-50 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    } text-white`;
    
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        alertDiv.classList.add('opacity-0', 'transition-opacity', 'duration-500');
        setTimeout(() => {
            document.body.removeChild(alertDiv);
        }, 500);
    }, 5000);
}

// Format date to display in a user-friendly format
function formatDate(dateString) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Format time to display in a user-friendly format (12-hour clock)
function formatTime(timeString) {
    if (!timeString) return '';
    
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    
    return `${hour12}:${minutes} ${ampm}`;
}

// Handle form validation errors
function displayFormErrors(form, errors) {
    // Clear previous errors
    form.querySelectorAll('.form-error').forEach(el => el.remove());
    
    // Display new errors
    for (const field in errors) {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            const errorElement = document.createElement('p');
            errorElement.className = 'form-error';
            errorElement.textContent = errors[field].join(' ');
            input.parentNode.insertBefore(errorElement, input.nextSibling);
        }
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Set up AJAX
    setupAjax();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Add event listeners for search form
    const searchForm = document.getElementById('doctor-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // Form will submit normally, but we could add validation here
        });
    }
    
    // Handle navigation menu toggle for mobile
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Format dates and times on the page
    document.querySelectorAll('.format-date').forEach(el => {
        el.textContent = formatDate(el.textContent);
    });
    
    document.querySelectorAll('.format-time').forEach(el => {
        el.textContent = formatTime(el.textContent);
    });
    
    // Handle appointment booking buttons
    document.querySelectorAll('.book-slot-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const slotId = this.dataset.slotId;
            const isAuthenticated = this.dataset.authenticated === 'true';
            
            if (!isAuthenticated) {
                e.preventDefault();
                // Save the slot ID in localStorage to redirect after login
                localStorage.setItem('pendingBookingSlot', slotId);
                window.location.href = '/auth/login/?next=/consultation/appointment/book/' + slotId + '/';
            }
        });
    });
    
    // Check if we need to redirect for booking after login
    const pendingBookingSlot = localStorage.getItem('pendingBookingSlot');
    if (pendingBookingSlot && document.body.classList.contains('logged-in')) {
        localStorage.removeItem('pendingBookingSlot');
        window.location.href = '/consultation/appointment/book/' + pendingBookingSlot + '/';
    }
});
