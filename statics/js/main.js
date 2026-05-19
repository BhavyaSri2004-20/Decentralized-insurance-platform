// Main JavaScript for Decentralized Insurance Platform

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        });
    }, 5000);

    // File upload drag and drop functionality
    initializeFileUpload();

    // Form validation
    initializeFormValidation();

    // Copy to clipboard functionality
    initializeCopyToClipboard();

    // Real-time updates simulation
    initializeRealTimeUpdates();
});

// File Upload Drag and Drop
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        const fileUploadArea = input.parentElement;
        
        // Add drag over event
        fileUploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });

        // Add drag leave event
        fileUploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });

        // Add drop event
        fileUploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                updateFileName(input);
            }
        });

        // Add change event
        input.addEventListener('change', function() {
            updateFileName(this);
        });
    });
}

function updateFileName(input) {
    const files = input.files;
    const label = input.parentElement.querySelector('.file-label') || 
                  input.parentElement.querySelector('label');
    
    if (files.length > 0) {
        if (label) {
            label.textContent = files[0].name;
        }
        
        // Add visual feedback
        input.parentElement.classList.add('file-selected');
        
        // Show file size
        const fileSize = formatFileSize(files[0].size);
        showFileInfo(input.parentElement, files[0].name, fileSize);
    } else {
        if (label) {
            const defaultText = label.getAttribute('data-default') || 
                               'Choose file';
            label.textContent = defaultText;
        }
        input.parentElement.classList.remove('file-selected');
    }
}

function showFileInfo(container, filename, size) {
    let infoElement = container.querySelector('.file-info');
    if (!infoElement) {
        infoElement = document.createElement('div');
        infoElement.className = 'file-info mt-2';
        container.appendChild(infoElement);
    }
    infoElement.innerHTML = `
        <small class="text-success">
            <i class="fas fa-check-circle"></i> ${filename} (${size})
        </small>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        const value = field.value.trim();
        const fieldContainer = field.closest('.mb-3') || field.closest('.form-group');
        
        // Remove existing error styling
        field.classList.remove('is-invalid', 'border-danger');
        if (fieldContainer) {
            const errorElement = fieldContainer.querySelector('.error-message');
            if (errorElement) {
                errorElement.remove();
            }
        }
        
        if (!value) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else if (field.type === 'email' && !isValidEmail(value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        } else if (field.type === 'tel' && !isValidPhone(value)) {
            showFieldError(field, 'Please enter a valid phone number');
            isValid = false;
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid', 'border-danger');
    const fieldContainer = field.closest('.mb-3') || field.closest('.form-group');
    
    if (fieldContainer) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message text-danger small mt-1';
        errorElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        fieldContainer.appendChild(errorElement);
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

// Copy to Clipboard
function initializeCopyToClipboard() {
    const copyButtons = document.querySelectorAll('.copy-to-clipboard');
    
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-text') || 
                              document.querySelector(this.getAttribute('data-target')).textContent;
            
            copyToClipboard(textToCopy);
            
            // Show feedback
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Copied!';
            this.classList.add('btn-success');
            
            setTimeout(() => {
                this.innerHTML = originalText;
                this.classList.remove('btn-success');
            }, 2000);
        });
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}

// Real-time Updates Simulation
function initializeRealTimeUpdates() {
    // Simulate real-time status updates for claims and policies
    const statusElements = document.querySelectorAll('.status-update');
    
    statusElements.forEach(function(element) {
        const currentStatus = element.textContent.trim();
        const lastUpdate = element.getAttribute('data-last-update');
        
        if (shouldUpdateStatus(currentStatus, lastUpdate)) {
            showUpdateNotification(element, generateStatusUpdate());
        }
    });
}

function shouldUpdateStatus(currentStatus, lastUpdate) {
    if (!lastUpdate) return true;
    
    const lastUpdateTime = new Date(lastUpdate);
    const now = new Date();
    const timeDiff = now - lastUpdateTime;
    
    // Update every 30 seconds for pending items
    return timeDiff > 30000;
}

function showUpdateNotification(element, newStatus) {
    const originalText = element.textContent;
    element.textContent = newStatus;
    element.classList.add('text-success');
    element.setAttribute('data-last-update', new Date().toISOString());
    
    // Auto-revert after 3 seconds
    setTimeout(() => {
        element.textContent = originalText;
        element.classList.remove('text-success');
    }, 3000);
}

function generateStatusUpdate() {
    const updates = [
        'Processing...',
        'Under Review',
        'Awaiting Approval',
        'Approved',
        'Payment Processed'
    ];
    return updates[Math.floor(Math.random() * updates.length)];
}

// Blockchain Hash Formatting
function formatBlockchainHash(hash) {
    if (!hash) return 'N/A';
    
    if (hash.length > 20) {
        return `${hash.substring(0, 10)}...${hash.substring(hash.length - 10)}`;
    }
    return hash;
}

// Payment Amount Formatting
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Date Formatting
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Search Functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetElements = document.querySelectorAll(this.getAttribute('data-target'));
            
            targetElements.forEach(function(element) {
                const text = element.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    element.style.display = '';
                } else {
                    element.style.display = 'none';
                }
            });
        });
    });
}

// Modal Management
function openModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function closeModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// Notification System
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

// Loading State Management
function showLoading(element, text = 'Loading...') {
    const originalContent = element.innerHTML;
    element.setAttribute('data-original-content', originalContent);
    element.innerHTML = `
        <span class="loading"></span> ${text}
    `;
    element.disabled = true;
}

function hideLoading(element) {
    const originalContent = element.getAttribute('data-original-content');
    if (originalContent) {
        element.innerHTML = originalContent;
        element.removeAttribute('data-original-content');
        element.disabled = false;
    }
}

// Export functions for global use
window.InsuranceApp = {
    formatCurrency,
    formatDate,
    formatBlockchainHash,
    showNotification,
    showLoading,
    hideLoading,
    openModal,
    closeModal
};