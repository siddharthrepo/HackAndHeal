/**
 * Main JavaScript file for HealthMeter
 */

// =====================
// Dark Mode
// =====================
function initDarkMode() {
    var theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else if (theme === 'light') {
        document.documentElement.classList.remove('dark');
    }
    // If no theme stored, the inline script in <head> already handled system preference
}

function toggleDarkMode() {
    var html = document.documentElement;
    if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
}

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

// Show notifications (dark mode aware)
function showNotification(message, type = 'info') {
    var isDark = document.documentElement.classList.contains('dark');
    var bgColors = {
        success: isDark ? 'bg-emerald-800 border border-emerald-600' : 'bg-emerald-500',
        error: isDark ? 'bg-red-800 border border-red-600' : 'bg-red-500',
        warning: isDark ? 'bg-amber-800 border border-amber-600' : 'bg-amber-500',
        info: isDark ? 'bg-indigo-800 border border-indigo-600' : 'bg-indigo-500'
    };

    const alertDiv = document.createElement('div');
    alertDiv.className = 'fixed top-4 right-4 p-4 rounded-xl shadow-lg z-50 ' +
        (bgColors[type] || bgColors.info) + ' text-white backdrop-blur-sm';

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
    // Initialize dark mode
    initDarkMode();

    // Bind dark mode toggles
    var toggleBtn = document.getElementById('dark-mode-toggle');
    var toggleBtnMobile = document.getElementById('dark-mode-toggle-mobile');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleDarkMode);
    if (toggleBtnMobile) toggleBtnMobile.addEventListener('click', toggleDarkMode);

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

    // Auto-hide header on scroll down, show on scroll up
    (function() {
        var header = document.querySelector('.c360-header');
        if (!header) return;
        var lastScrollY = window.scrollY;
        var ticking = false;

        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    var currentScrollY = window.scrollY;
                    if (currentScrollY > lastScrollY && currentScrollY > 80) {
                        header.classList.add('header-hidden');
                    } else {
                        header.classList.remove('header-hidden');
                    }
                    lastScrollY = currentScrollY;
                    ticking = false;
                });
                ticking = true;
            }
        });
    })();

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
