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

    showAlert(`Selected worklist: ${worklistName}`, 'info');
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
        showAlert('Please select a target worklist first', 'warning');
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

// Subscribe/unsubscribe to worklists
function toggleSubscription(worklistId, subscribe) {
    const action = subscribe ? 'subscribe_to_worklist' : 'unsubscribe_worklist';
    const data = subscribe ?
        { user_id: window.currentUserId, worklist_id: worklistId } :
        { user_id: window.currentUserId, worklist_id: worklistId };

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
