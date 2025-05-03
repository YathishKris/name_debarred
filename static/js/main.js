// Main JavaScript for Debarred Entities Downloader

// Close alerts automatically after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Auto-close alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alert.classList.add('fade');
                setTimeout(function() {
                    alert.remove();
                }, 150);
            }
        }, 5000);
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Date range validation for report filters
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (dateFromInput && dateToInput) {
        dateFromInput.addEventListener('change', validateDateRange);
        dateToInput.addEventListener('change', validateDateRange);
        
        function validateDateRange() {
            if (dateFromInput.value && dateToInput.value) {
                const fromDate = new Date(dateFromInput.value);
                const toDate = new Date(dateToInput.value);
                
                if (fromDate > toDate) {
                    dateToInput.setCustomValidity('To date must be after from date');
                } else {
                    dateToInput.setCustomValidity('');
                }
            } else {
                dateToInput.setCustomValidity('');
            }
        }
    }
    
    // Settings form validation
    const settingsForm = document.querySelector('form[action*="settings"]');
    
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(event) {
            const hourInput = document.getElementById('hour');
            const minuteInput = document.getElementById('minute');
            const retryAttemptsInput = document.getElementById('retry_attempts');
            const retryDelayInput = document.getElementById('retry_delay');
            
            let isValid = true;
            
            // Validate hour (0-23)
            const hour = parseInt(hourInput.value);
            if (isNaN(hour) || hour < 0 || hour > 23) {
                hourInput.setCustomValidity('Hour must be between 0 and 23');
                isValid = false;
            } else {
                hourInput.setCustomValidity('');
            }
            
            // Validate minute (0-59)
            const minute = parseInt(minuteInput.value);
            if (isNaN(minute) || minute < 0 || minute > 59) {
                minuteInput.setCustomValidity('Minute must be between 0 and 59');
                isValid = false;
            } else {
                minuteInput.setCustomValidity('');
            }
            
            // Validate retry attempts (1-10)
            const retryAttempts = parseInt(retryAttemptsInput.value);
            if (isNaN(retryAttempts) || retryAttempts < 1 || retryAttempts > 10) {
                retryAttemptsInput.setCustomValidity('Retry attempts must be between 1 and 10');
                isValid = false;
            } else {
                retryAttemptsInput.setCustomValidity('');
            }
            
            // Validate retry delay (1-60)
            const retryDelay = parseInt(retryDelayInput.value);
            if (isNaN(retryDelay) || retryDelay < 1 || retryDelay > 60) {
                retryDelayInput.setCustomValidity('Retry delay must be between 1 and 60 minutes');
                isValid = false;
            } else {
                retryDelayInput.setCustomValidity('');
            }
            
            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    }
    
    // Add confirmation for "Run Now" button
    const runNowForm = document.querySelector('form[action*="run-now"]');
    
    if (runNowForm) {
        runNowForm.addEventListener('submit', function(event) {
            if (!confirm('Are you sure you want to run the download job now?')) {
                event.preventDefault();
            }
        });
    }
});
