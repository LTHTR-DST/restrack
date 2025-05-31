// ResTrack JavaScript functionality

let selectedOrders = new Set();
let currentWorklistId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    // Setup htmx event listeners
    setupHtmxEvents();
});

function setupHtmxEvents() {
    // Show loading indicator on htmx requests
    document.body.addEventListener('htmx:beforeRequest', function (event) {
        const loadingEl = document.querySelector('.loading');
        if (loadingEl) {
            loadingEl.style.display = 'block';
        }
    });

    // Hide loading indicator when request completes
    document.body.addEventListener('htmx:afterRequest', function (event) {
        const loadingEl = document.querySelector('.loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    });

    // Handle successful responses
    document.body.addEventListener('htmx:afterSwap', function (event) {
        // Reinitialize any components after content swap
        initializeTableCheckboxes();
        updateAddToWorklistButton();
    });
}

// Worklist selection
function selectWorklist(worklistId, worklistName) {
    currentWorklistId = worklistId;
    selectedOrders.clear();
    updateAddToWorklistButton();

    // Update active worklist in sidebar
    document.querySelectorAll('.worklist-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-worklist-id="${worklistId}"]`).classList.add('active');

    // Load orders for this worklist
    htmx.ajax('GET', `/worklists/${worklistId}/orders`, { target: '#orders-table' });

    // Show toast notification instead of alert
    showToast(`Selected worklist: ${worklistName}`, 'info');
}

// Order selection handling
function initializeTableCheckboxes() {
    const checkboxes = document.querySelectorAll('.order-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const orderId = parseInt(this.value);
            const row = this.closest('tr');

            if (this.checked) {
                selectedOrders.add(orderId);
                row.classList.add('table-active');
            } else {
                selectedOrders.delete(orderId);
                row.classList.remove('table-active');
            }

            updateAddToWorklistButton();
            updateActionButtons();
        });
    });

    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.order-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                const orderId = parseInt(checkbox.value);
                const row = checkbox.closest('tr');

                if (this.checked) {
                    selectedOrders.add(orderId);
                    row.classList.add('table-active');
                } else {
                    selectedOrders.delete(orderId);
                    row.classList.remove('table-active');
                }
            });

            updateAddToWorklistButton();
            updateActionButtons();
        });
    }
}

function updateAddToWorklistButton() {
    const addBtn = document.getElementById('add-to-worklist-btn');
    if (addBtn) {
        addBtn.disabled = selectedOrders.size === 0 || !currentWorklistId;
    }
}

function updateActionButtons() {
    const hasSelection = selectedOrders.size > 0;

    const statusSelect = document.getElementById('status-select');
    const noteInput = document.getElementById('note-input');

    if (statusSelect) statusSelect.disabled = !hasSelection;
    if (noteInput) noteInput.disabled = !hasSelection;

    // Update button states
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(btn => {
        btn.disabled = !hasSelection;
    });
}

// Add selected orders to current worklist
function addSelectedToWorklist() {
    if (selectedOrders.size === 0 || !currentWorklistId) {
        showAlert('Please select orders and a worklist', 'warning');
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/add_to_worklist/' + encodeURIComponent(JSON.stringify({
        worklist_id: currentWorklistId,
        order_ids: orderIds
    })), {
        method: 'PUT'
    })
        .then(response => response.json())
        .then(success => {
            if (success) {
                showAlert(`Added ${orderIds.length} orders to worklist`, 'success');
                selectedOrders.clear();
                updateAddToWorklistButton();
                // Refresh current worklist if it's selected
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showAlert('Failed to add orders to worklist', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error adding orders to worklist', 'danger');
        });
}

// Update order status
function updateOrderStatus() {
    const statusSelect = document.getElementById('status-select');
    const selectedStatus = statusSelect.value;

    if (!selectedStatus || selectedOrders.size === 0) {
        showAlert('Please select orders and a status', 'warning');
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/comment_orders/' + encodeURIComponent(JSON.stringify({
        action: selectedStatus,
        order_ids: orderIds
    })), {
        method: 'PUT'
    })
        .then(response => {
            if (response.ok) {
                showAlert(`Updated status for ${orderIds.length} orders`, 'success');
                statusSelect.value = '';
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showAlert('Failed to update order status', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error updating order status', 'danger');
        });
}

// Add note to orders
function addNote() {
    const noteInput = document.getElementById('note-input');
    const noteText = noteInput.value.trim();

    if (!noteText || selectedOrders.size === 0 || !currentWorklistId) {
        showAlert('Please select orders, enter a note, and select a worklist', 'warning');
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/annotate_worklist_orders/' + encodeURIComponent(JSON.stringify({
        note_text: noteText,
        order_ids: orderIds,
        worklist_id: currentWorklistId
    })), {
        method: 'POST'
    })
        .then(response => {
            if (response.ok) {
                showAlert(`Added note to ${orderIds.length} orders`, 'success');
                noteInput.value = '';
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showAlert('Failed to add note', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error adding note', 'danger');
        });
}

// Remove orders from worklist
function removeFromWorklist() {
    if (selectedOrders.size === 0 || !currentWorklistId) {
        showAlert('Please select orders to remove', 'warning');
        return;
    }

    if (!confirm(`Remove ${selectedOrders.size} orders from worklist?`)) {
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/remove_order_from_worklist/' + encodeURIComponent(JSON.stringify({
        worklist_id: currentWorklistId,
        order_ids: orderIds
    })), {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                showAlert(`Removed ${orderIds.length} orders from worklist`, 'success');
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
            } else {
                showAlert('Failed to remove orders', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error removing orders', 'danger');
        });
}

// Copy worklist
function copyWorklist(sourceWorklistId) {
    if (!currentWorklistId) {
        showAlert('Please select a target worklist first by clicking on a worklist in the sidebar', 'warning');
        return;
    }

    // Don't copy to the same worklist
    if (sourceWorklistId === currentWorklistId) {
        showAlert('Cannot copy a worklist to itself', 'warning');
        return;
    }

    if (!confirm('Copy all orders from selected worklist to current worklist?')) {
        return;
    }

    fetch('/api/v1/copy_worklist/' + encodeURIComponent(JSON.stringify({
        worklist_to_copy_from: sourceWorklistId,
        current_worklist: currentWorklistId
    })), {
        method: 'POST'
    })
        .then(response => {
            if (response.ok) {
                showAlert('Worklist copied successfully', 'success');
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showAlert('Failed to copy worklist', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error copying worklist', 'danger');
        });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertArea = document.getElementById('alert-area');
    if (!alertArea) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertArea.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Show toast notification (for non-intrusive messages)
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    // Create toast HTML
    const toastDiv = document.createElement('div');
    toastDiv.className = `toast show`;
    toastDiv.setAttribute('role', 'alert');
    toastDiv.setAttribute('aria-live', 'assertive');
    toastDiv.setAttribute('aria-atomic', 'true');

    // Set toast background based on type
    let bgClass = 'bg-primary';
    let textClass = 'text-white';
    if (type === 'success') bgClass = 'bg-success';
    else if (type === 'warning') bgClass = 'bg-warning';
    else if (type === 'danger') bgClass = 'bg-danger';
    else if (type === 'info') bgClass = 'bg-info';

    toastDiv.innerHTML = `
        <div class="toast-header ${bgClass} ${textClass}">
            <i class="bi bi-info-circle-fill me-2"></i>
            <strong class="me-auto">ResTrack</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    toastContainer.appendChild(toastDiv);

    // Initialize Bootstrap toast
    const toast = new bootstrap.Toast(toastDiv, {
        autohide: true,
        delay: 3000
    });

    toast.show();

    // Remove toast element after it's hidden
    toastDiv.addEventListener('hidden.bs.toast', () => {
        toastDiv.remove();
    });
}

// Subscribe/unsubscribe to worklists
function toggleSubscription(worklistId, subscribe) {
    // Get current user ID from data attribute
    const userId = document.body.getAttribute('data-user-id');

    if (!userId) {
        showAlert('User ID not found, please refresh the page or log in again', 'danger');
        return;
    }

    const action = subscribe ? 'subscribe_to_worklist' : 'unsubscribe_worklist';
    const data = subscribe ?
        { user_id: parseInt(userId), worklist_id: worklistId } :
        { user_id: parseInt(userId), worklist_id: worklistId };

    const method = subscribe ? 'PUT' : 'DELETE';

    fetch(`/api/v1/${action}/` + encodeURIComponent(JSON.stringify(data)), {
        method: method
    })
        .then(response => {
            if (response.ok) {
                showAlert(`${subscribe ? 'Subscribed to' : 'Unsubscribed from'} worklist`, 'success');
                // Refresh worklist selector and subscription manager
                htmx.ajax('GET', '/worklists/selector', { target: '#worklist-selector' });
                htmx.ajax('GET', '/worklists/subscription-manager', { target: '#subscription-manager' });
            } else {
                showAlert(`Failed to ${subscribe ? 'subscribe to' : 'unsubscribe from'} worklist`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error updating subscription', 'danger');
        });
}
