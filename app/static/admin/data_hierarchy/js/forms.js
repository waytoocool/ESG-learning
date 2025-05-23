console.log('forms.js loaded')

// This function will be responsible for handling the submission of the "Create New Entity" form --- Show popup
export function handleFormSubmit(event) {
    event.preventDefault();
    const form = document.getElementById('entity-form');
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = 'Saving...';

    fetch(form.getAttribute('action'), {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPopup('Success', data.message, 'success');
            document.getElementById("entity-drawer").style.display = "none";
            // Reset form
            form.reset();
            // Reload page after a short delay
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showPopup('Error', data.message || 'An error occurred while saving the entity.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPopup('Error', 'An error occurred while saving the entity.', 'error');
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Save';
    });
}

// This function will be responsible for handling the submission of the "Create New User" form. -- Show pop up
export function handleUserFormSubmit(event) {
    // Similar update to handleFormSubmit
    event.preventDefault();
    const form = document.getElementById('user-form');
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = 'Saving...';
    const createUserUrl = document.getElementById('user-form').getAttribute('action');

    fetch(createUserUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
    if (!response.ok) {
        // If response isn't ok, throw error to be caught by catch block
        throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showPopup('Success', data.message, 'success');
            document.getElementById("user-drawer").style.display = "none";
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showPopup('Error', data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPopup('Error', 'An error occurred while saving the user.', 'error');
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Save';
    });

    return false;
}

// This function is responsible for handling the resending of the user verification email
function handleVerificationResend(email) {
    const cooldownKey = `resend_cooldown_${email}`;

    // Check if there's an active cooldown
    if (localStorage.getItem(cooldownKey)) {
        showPopup('Notice', 'A verification email was recently sent. Please wait before requesting another one.', 'notice');
        return;
    }

    fetch("{{ url_for('resend_verification') }}", {
        method: 'POST',
        body: JSON.stringify({ email: email }),
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Set cooldown in localStorage
            localStorage.setItem(cooldownKey, 'true');

            // Remove cooldown after 15 minutes
            setTimeout(() => {
                localStorage.removeItem(cooldownKey);
            }, 15 * 60 * 1000);

            showPopup('Success', 'Verification email has been sent successfully', 'success');

            // Refresh the display to update the UI
            if (activeNodeId) {
                const node = d3.select(`[data-id="${activeNodeId}"]`).datum();
                if (displayMode === 'sidebar') {
                    showSidebar(node);
                } else {
                    showStickyDetails(event, node);
                }
            }
        } else {
            showPopup('Error', data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPopup('Error', 'An error occurred while resending verification email.', 'error');
    });
}

// This function is responsible for displaying the notification popup
function showPopup(title, message, type = 'notice') {
    const popup = document.getElementById('notificationPopup');
    const titleElement = document.getElementById('popupTitle');
    const messageElement = document.getElementById('popupMessage');

    // Reset classes
    popup.className = 'popup-message';

    // Add type class
    popup.classList.add(type);

    // Set content
    titleElement.textContent = title;
    messageElement.textContent = message;

    // Show popup
    popup.classList.add('show');

    // Auto-hide after 4 seconds
    setTimeout(() => {
        closePopup();
    }, 4000);
}

// This function is responsible for hiding the notification popup
function closePopup() {
    const popup = document.getElementById('notificationPopup');
    popup.classList.add('hide');

    // Remove show and hide classes after animation
    popup.addEventListener('animationend', () => {
        popup.classList.remove('show', 'hide');
    }, { once: true }); // Ensure event listener is removed after execution
}