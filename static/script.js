// Enhanced Library Management System JavaScript
document.addEventListener("DOMContentLoaded", function() {
    initializeApp();
});

function initializeApp() {
    // Initialize all components
    initializeFlashMessages();
    initializeCharts();
    initializeSidebar();
    initializeDarkMode();
    initializeAnimations();
    initializeFormEnhancements();
    initializeTableEnhancements();
}

// Enhanced Flash Messages with better animations
function initializeFlashMessages() {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach((flash, index) => {
        // Stagger the animation
        flash.style.animationDelay = `${index * 0.1}s`;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            flash.style.transition = "all 0.5s cubic-bezier(0.4, 0, 0.2, 1)";
            flash.style.transform = "translateX(100%)";
            flash.style.opacity = "0";
            setTimeout(() => flash.remove(), 500);
        }, 5000);
        
        // Add click to dismiss
        flash.addEventListener('click', () => {
            flash.style.transition = "all 0.3s ease";
            flash.style.transform = "translateX(100%)";
            flash.style.opacity = "0";
            setTimeout(() => flash.remove(), 300);
        });
    });
}

// Enhanced Charts with better styling
function initializeCharts() {
    const pieCanvas = document.getElementById("pieChart");
    if(pieCanvas) {
        new Chart(pieCanvas, {
            type: 'doughnut',
            data: {
                labels: JSON.parse(pieCanvas.dataset.labels),
                datasets: [{
                    data: JSON.parse(pieCanvas.dataset.values),
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', 
                        '#ef4444', '#8b5cf6', '#06b6d4'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    animateScale: true,
                    duration: 1500,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    const barCanvas = document.getElementById("barChart");
    if(barCanvas) {
        new Chart(barCanvas, {
            type: 'bar',
            data: {
                labels: JSON.parse(barCanvas.dataset.labels),
                datasets: [{
                    label: 'Number of Issues',
                    data: JSON.parse(barCanvas.dataset.values),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1500,
                    easing: 'easeOutBounce'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        precision: 0,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Enhanced Sidebar functionality
function initializeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    // Mobile sidebar handling
    if (window.innerWidth <= 768) {
        sidebar.classList.add('mobile');
    }
    
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('mobile');
        } else {
            sidebar.classList.remove('mobile');
        }
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            !sidebar.contains(e.target) && 
            !toggleBtn.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// Enhanced Dark Mode with localStorage persistence
function initializeDarkMode() {
    const darkModeToggle = document.querySelector('#darkToggle');
    // Ensure button reflects current state
    const isDark = document.documentElement.classList.contains('dark-mode');
    updateDarkModeButton(isDark);
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            toggleDarkMode();
        });
    }
}

// Enhanced Dark Mode Toggle
function toggleDarkMode() {
    // Use documentElement to avoid depending on body class
    const root = document.documentElement;
    const isDark = root.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateDarkModeButton(isDark);
    
    // Add a subtle animation
    root.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
}

function updateDarkModeButton(isDark) {
    const toggle = document.querySelector('#darkToggle');
    if (toggle) {
        toggle.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
        toggle.setAttribute('aria-pressed', String(isDark));
    }
}

// Enhanced Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const isCollapsed = sidebar.classList.contains('collapsed');
    
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
    } else {
        sidebar.classList.toggle('collapsed');
    }
    
    // Add animation class
    sidebar.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
}

// Initialize page animations
function initializeAnimations() {
    // Animate cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards';
            }
        });
    }, observerOptions);
    
    // Observe all cards
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
    
    // Add loading animation to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.classList.contains('disabled')) {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            }
        });
    });
}

// Enhanced form functionality
function initializeFormEnhancements() {
    // Add floating labels effect
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if input has value on load
        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });
    
    // Add form validation feedback
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#ef4444';
                    isValid = false;
                } else {
                    field.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'error');
            }
        });
    });
    // (Reverted) Instant search removed
}

// Enhanced table functionality
function initializeTableEnhancements() {
    // Add hover effects to table rows
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// Utility function for notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash flash-${type}`;
    notification.textContent = message;
    
    const container = document.getElementById('flash-messages') || createFlashContainer();
    container.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease';
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.id = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading states for forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.style.opacity = '0.7';
            submitBtn.style.pointerEvents = 'none';
            submitBtn.textContent = 'Processing...';
        }
    });
});
