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
            window.PopupManager?.showSuccess('Success', data.message) || console.log('Success:', data.message);
            document.getElementById("entity-drawer").style.display = "none";
            // Reset form
            form.reset();
            // Reload page after a short delay
            setTimeout(() => window.location.reload(), 1000);
        } else {
            window.PopupManager?.showError('Error', data.message || 'An error occurred while saving the entity.') || console.error('Error:', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.PopupManager?.showError('Error', 'An error occurred while saving the entity.') || console.error('Error occurred');
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
    .then(async response => {
        // Always attempt to parse JSON so we can surface detailed error messages
        let data = {};
        try {
            data = await response.json();
        } catch (e) {
            console.warn('Could not parse JSON from create_user response');
        }

        if (response.ok && data.success) {
            window.PopupManager?.showSuccess('Success', data.message || 'User created successfully') || console.log('Success:', data.message);
            document.getElementById("user-drawer").style.display = "none";
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const msg = data.message || `Server returned HTTP ${response.status}`;
            window.PopupManager?.showError('Error', msg) || console.error('Error:', msg);
            throw new Error(msg); // Ensure catch() gets triggered for logging
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (!window.PopupManager) {
            alert('Error creating user: ' + error.message);
        }
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Save';
    });

    return false;
}

// This function is responsible for handling the resending of the user verification email
export function handleVerificationResend(email) {
    const cooldownKey = `resend_cooldown_${email}`;

    // Check if there's an active cooldown
    if (localStorage.getItem(cooldownKey)) {
        window.PopupManager?.showWarning('Notice', 'A verification email was recently sent. Please wait before requesting another one.') || console.log('Cooldown active');
        return;
    }

    // Use the Flask route path directly; this static file is not rendered by Jinja
    // so we cannot rely on "{{ url_for(...) }}".  The Blueprint is registered
    // under /admin so the final URL is /admin/resend_verification.
    fetch('/admin/resend_verification', {
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

            window.PopupManager?.showSuccess('Success', 'Verification email has been sent successfully') || console.log('Verification email sent');

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
            window.PopupManager?.showError('Error', data.message) || console.error('Error:', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.PopupManager?.showError('Error', 'An error occurred while resending verification email.') || console.error('Error occurred');
    });
}

// Make it available for inline onClick handlers created in HTML strings
if (typeof window !== 'undefined') {
    window.handleVerificationResend = handleVerificationResend;
}