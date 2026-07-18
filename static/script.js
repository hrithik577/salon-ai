// MANJUNATH HAIR SALON - Main JavaScript

// Dark/Light Mode Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeToggleIcon(savedTheme);
    }

    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggleIcon(newTheme);
        });
    }
});

function updateThemeToggleIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    }
}

// Queue Auto-Refresh (every 10 seconds)
let refreshInterval;

function startQueueAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    refreshInterval = setInterval(function() {
        if (document.querySelector('#queue-status')) {
            updateQueueStatus();
        }
    }, 10000);
}

function stopQueueAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Update Queue Status via AJAX
function updateQueueStatus() {
    fetch('/api/queue/status')
        .then(response => response.json())
        .then(data => {
            // Update queue length
            const queueLength = document.querySelector('#queue-length');
            if (queueLength) {
                queueLength.textContent = data.queue_length;
            }

            // Update queue entries
            const queueList = document.querySelector('#queue-list');
            if (queueList) {
                queueList.innerHTML = '';
                data.entries.forEach(entry => {
                    const item = document.createElement('div');
                    item.className = 'queue-item fade-in';
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="position-badge">#${entry.position}</span>
                                <strong>${entry.user_name}</strong>
                                <span class="text-muted ms-2">${entry.service_name}</span>
                            </div>
                            <div>
                                <span class="wait-time">~${entry.estimated_wait} min</span>
                            </div>
                        </div>
                    `;
                    queueList.appendChild(item);
                });
            }

            // Update busy hours
            const busyHours = document.querySelector('#busy-hours');
            if (busyHours && data.busy_hours) {
                busyHours.textContent = data.busy_hours.map(h =>
                    h < 12 ? `${h}:00 AM` : h === 12 ? '12:00 PM' : `${h-12}:00 PM`
                ).join(', ');
            }
        })
        .catch(error => console.error('Error updating queue:', error));
}

// Queue page specific functions
function joinQueue() {
    const serviceSelect = document.querySelector('#service-select');
    if (!serviceSelect || !serviceSelect.value) {
        alert('Please select a service');
        return;
    }

    document.querySelector('#join-queue-form').submit();
}

function leaveQueue(queueId) {
    if (!confirm('Are you sure you want to leave the queue?')) {
        return;
    }

    fetch(`/api/queue/leave/${queueId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('You have left the queue');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
}

// Admin functions
function nextCustomer() {
    if (!confirm('Ready to call the next customer?')) {
        return;
    }

    fetch('/api/queue/next')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
}

function deleteService(serviceId) {
    if (!confirm('Are you sure you want to delete this service?')) {
        return;
    }

    // Implement service deletion
    // This would require an API endpoint
    alert('Service deletion would be implemented with an API endpoint');
}

// Form Validation
function validateForm(formId) {
    const form = document.querySelector(`#${formId}`);
    if (!form) return true;

    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    // Password confirmation
    const password = form.querySelector('#password');
    const confirmPassword = form.querySelector('#confirm_password');
    if (password && confirmPassword) {
        if (password.value !== confirmPassword.value) {
            confirmPassword.classList.add('is-invalid');
            isValid = false;
        } else {
            confirmPassword.classList.remove('is-invalid');
        }
    }

    // Email validation
    const email = form.querySelector('#email');
    if (email && email.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
            email.classList.add('is-invalid');
            isValid = false;
        } else {
            email.classList.remove('is-invalid');
        }
    }

    return isValid;
}

// Auto-dismiss alerts
setTimeout(function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-persistent')) {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }, 5000);
        }
    });
}, 1000);

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Initialize auto-refresh on queue page
if (window.location.pathname.includes('/queue')) {
    startQueueAutoRefresh();
    updateQueueStatus();
}

// Dashboard chart (placeholder for future implementation)
function initializeCharts() {
    // This would be implemented with a charting library like Chart.js
    console.log('Charts initialized (placeholder)');
}

// Print friendly function
function printPage() {
    window.print();
}

// Mobile menu toggle enhancement
document.addEventListener('click', function(e) {
    const navbar = document.querySelector('.navbar-collapse');
    if (navbar && navbar.classList.contains('show')) {
        const isNavbarClick = navbar.contains(e.target) || e.target.closest('.navbar-toggler');
        if (!isNavbarClick) {
            navbar.classList.remove('show');
        }
    }
});

// Loading state for buttons
document.querySelectorAll('button[type="submit"], .btn-submit').forEach(button => {
    button.addEventListener('click', function(e) {
        if (this.closest('form') && !this.closest('form').checkValidity()) {
            return;
        }
        const originalText = this.innerHTML;
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

        // Re-enable after 3 seconds or on form submission
        setTimeout(() => {
            this.disabled = false;
            this.innerHTML = originalText;
        }, 3000);
    });
});