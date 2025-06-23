// ResTrack JavaScript functionality

let selectedOrders = new Set();
let currentWorklistId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded');
    // Setup htmx event listeners
    setupHtmxEvents();
    
    // Check if button exists on page load
    const btn = document.getElementById('toggle-complete-btn');
    console.log('Button exists on page load:', !!btn);
    if (btn) {
        console.log('Button text:', btn.textContent);
    }
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
        
        // Check if the swapped content is a patient orders table
        if (event.detail.target.id === 'orders-table') {
            const isPatientView = event.detail.target.querySelector('[data-view-type="patient-orders"]') !== null;
            toggleWorklistActions(!isPatientView && currentWorklistId);
        }
    });
}

// Worklist selection
function selectWorklist(worklistId, worklistName) {
    currentWorklistId = worklistId;
    selectedOrders.clear();
    updateAddToWorklistButton();

    // Update selected worklist in sidebar
    document.querySelectorAll('.worklist-item').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`[data-worklist-id="${worklistId}"]`).classList.add('selected');

    // Show worklist actions since we're viewing a worklist
    toggleWorklistActions(true);

    // Load orders for this worklist
    htmx.ajax('GET', `/worklists/${worklistId}/orders`, { target: '#orders-table' });

    // Show toast notification instead of alert
    showToast(`Selected worklist: ${worklistName}`, 'info');
}

// Function to show/hide worklist actions
function toggleWorklistActions(show) {
    const actionsDiv = document.getElementById('worklist-actions');
    if (actionsDiv) {
        if (show) {
            actionsDiv.classList.remove('d-none');
            actionsDiv.classList.add('d-flex');
        } else {
            actionsDiv.classList.remove('d-flex');
            actionsDiv.classList.add('d-none');
        }
    }
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
        showToast('Please select orders and a worklist', 'warning');
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
                showToast(`Added ${orderIds.length} orders to worklist`, 'success');
                selectedOrders.clear();
                updateAddToWorklistButton();
                // Refresh current worklist if it's selected
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showToast('Failed to add orders to worklist', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error adding orders to worklist', 'danger');
        });
}

// Update order status
function updateOrderStatus() {
    const statusSelect = document.getElementById('status-select');
    const selectedStatus = statusSelect.value;

    if (!selectedStatus || selectedOrders.size === 0) {
        showToast('Please select orders and a status', 'warning');
        return;
    }

    const orderIds = Array.from(selectedOrders); fetch('/api/v1/comment/' + encodeURIComponent(JSON.stringify({
        action: selectedStatus,
        order_ids: orderIds
    })), {
        method: 'PUT'
    })
        .then(response => {
            if (response.ok) {
                showToast(`Updated status for ${orderIds.length} orders`, 'success');
                statusSelect.value = '';
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showToast('Failed to update order status', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating order status', 'danger');
        });
}

// Add note to orders
function addNote() {
    const noteInput = document.getElementById('note-input');
    const noteText = noteInput.value.trim();

    if (!noteText || selectedOrders.size === 0 || !currentWorklistId) {
        showToast('Please select a worklist, orders, and enter a note', 'warning');
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/annotate/' + encodeURIComponent(JSON.stringify({
        note_text: noteText,
        order_ids: orderIds,
        worklist_id: currentWorklistId
    })), {
        method: 'POST'
    })
        .then(response => {
            if (response.ok) {
                showToast(`Added note to ${orderIds.length} orders`, 'success');
                noteInput.value = '';
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showToast('Failed to add note', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error adding note', 'danger');
        });
}

// Remove orders from worklist
function removeFromWorklist() {
    if (selectedOrders.size === 0 || !currentWorklistId) {
        showToast('Please select orders to remove', 'warning');
        return;
    }

    if (!confirm(`Remove ${selectedOrders.size} orders from worklist?`)) {
        return;
    }

    const orderIds = Array.from(selectedOrders);

    fetch('/api/v1/remove_from_worklist/' + encodeURIComponent(JSON.stringify({
        worklist_id: currentWorklistId,
        order_ids: orderIds
    })), {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                showToast(`Removed ${orderIds.length} orders from worklist`, 'success');
                selectedOrders.clear();
                updateActionButtons();
                // Refresh current worklist
                htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
            } else {
                showToast('Failed to remove orders', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error removing orders', 'danger');
        });
}

// Copy worklist
function copyWorklist(sourceWorklistId) {
    if (!currentWorklistId) {
        showToast('Please select a target worklist first by clicking on a worklist in the sidebar', 'warning');
        return;
    }

    // Don't copy to the same worklist
    if (sourceWorklistId === currentWorklistId) {
        showToast('Cannot copy a worklist to itself', 'warning');
        return;
    }

    if (!confirm('Copy all orders from selected worklist to current worklist?')) {
        return;
    }

    fetch('/api/v1/worklists/copy/' + encodeURIComponent(JSON.stringify({
        worklist_to_copy_from: sourceWorklistId,
        current_worklist: currentWorklistId
    })), {
        method: 'POST'
    })
        .then(response => {
            if (response.ok) {
                showToast('Worklist copied successfully', 'success');
                // Refresh current worklist
                if (currentWorklistId) {
                    htmx.ajax('GET', `/worklists/${currentWorklistId}/orders`, { target: '#orders-table' });
                }
            } else {
                showToast('Failed to copy worklist', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error copying worklist', 'danger');
        });
}

// Show alert message
// function showAlert(message, type = 'info') {
//     const alertArea = document.getElementById('alert-area');
//     if (!alertArea) return;

//     const alertDiv = document.createElement('div');
//     alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
//     alertDiv.innerHTML = `
//         ${message}
//         <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
//     `;

//     alertArea.appendChild(alertDiv);

//     // Auto-dismiss after 5 seconds
//     setTimeout(() => {
//         if (alertDiv.parentNode) {
//             alertDiv.remove();
//         }
//     }, 5000);
// }

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
        showToast('User ID not found, please refresh the page or log in again', 'danger');
        return;
    }

    const action = subscribe ? 'worklists/subscribe' : 'worklists/unsubscribe';
    const data = subscribe ?
        { user_id: parseInt(userId), worklist_id: worklistId } :
        { user_id: parseInt(userId), worklist_id: worklistId };

    const method = subscribe ? 'PUT' : 'DELETE';

    fetch(`/api/v1/${action}/` + encodeURIComponent(JSON.stringify(data)), {
        method: method
    })
        .then(response => {
            if (response.ok) {
                showToast(`${subscribe ? 'Subscribed to' : 'Unsubscribed from'} worklist`, 'success');
                // Refresh worklist selector and subscription manager
                htmx.ajax('GET', '/worklists/selector/fast', { target: '#worklist-selector' });
                htmx.ajax('GET', '/worklists/subscription-manager', { target: '#subscription-manager' });
            } else {
                showToast(`Failed to ${subscribe ? 'subscribe to' : 'unsubscribe from'} worklist`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error updating subscription', 'danger');
        });
}

// Handle logout action
function handleLogout(event) {
    // Prevent default behavior
    event.preventDefault();

    // Show feedback
    showToast('Logging out...', 'info');

    // Navigate to the logout endpoint which will clear the token cookie
    window.location.href = '/logout';
}

// Toggle showing only complete orders or all orders
function toggleShowComplete() {
    console.log('toggleShowComplete called');
    const btn = document.getElementById('toggle-complete-btn');
    const table = document.querySelector('.orders-table');
    console.log('Button found:', !!btn, 'Table found:', !!table);
    if (!table || !btn) return;
    
    // Initialize the data attribute if it doesn't exist
    if (!btn.dataset.showComplete) {
        btn.dataset.showComplete = 'false';
    }
    
    const isCurrentlyShowingComplete = btn.dataset.showComplete === 'true';
    console.log('Currently showing complete:', isCurrentlyShowingComplete);
    const rows = table.querySelectorAll('tbody tr');
    console.log('Found', rows.length, 'rows');
    
    let processedRows = 0;
    rows.forEach((row, index) => {
        const tds = row.querySelectorAll('td');
        console.log(`Row ${index}: ${tds.length} cells`);
        if (tds.length < 5) {
            // Likely a group header or non-order row, always show
            row.style.display = '';
            return;
        }
        // Find the Order Status cell (5th td)
        const orderStatusCell = tds[4];
        if (!orderStatusCell) return;
        // Find the badge inside the Order Status cell
        const badge = orderStatusCell.querySelector('.badge');
        if (!badge) {
            console.log(`Row ${index}: No badge found in Order Status cell`);
            return;
        }
        // Check if the badge text is exactly 'complete' (case-insensitive)
        const statusText = badge.textContent.trim().toLowerCase();
        console.log(`Row ${index}: Status text = "${statusText}"`);
        const isComplete = statusText === 'complete';
        
        if (isCurrentlyShowingComplete) {
            // Currently showing only complete, so show all rows
            row.style.display = '';
        } else {
            // Currently showing all, so show only complete
            if (isComplete) {
                row.style.display = '';
                console.log(`Row ${index}: Showing (complete)`);
            } else {
                row.style.display = 'none';
                console.log(`Row ${index}: Hiding (not complete)`);
            }
        }
        processedRows++;
    });
    
    console.log('Processed', processedRows, 'data rows');
    
    // Toggle the state and update button text
    if (isCurrentlyShowingComplete) {
        btn.textContent = 'Show Complete';
        btn.dataset.showComplete = 'false';
        console.log('Button updated to: Show Complete');
    } else {
        btn.textContent = 'Show All';
        btn.dataset.showComplete = 'true';
        console.log('Button updated to: Show All');
    }
}

// Use event delegation for the Show Complete button
console.log('Setting up event delegation for Show Complete button');
document.addEventListener('click', function(event) {
    console.log('Click detected on:', event.target.tagName, event.target.id, event.target.className);
    const btn = event.target.closest('#toggle-complete-btn');
    if (btn) {
        console.log('Show Complete button clicked!');
        event.preventDefault();
        toggleShowComplete();
    } else if (event.target.id === 'toggle-complete-btn') {
        console.log('Direct click on toggle-complete-btn');
        event.preventDefault();
        toggleShowComplete();
    }
});

// Debug function to check button status - call this from console
window.debugShowCompleteButton = function() {
    const btn = document.getElementById('toggle-complete-btn');
    const table = document.querySelector('.orders-table');
    console.log('=== DEBUG INFO ===');
    console.log('Button exists:', !!btn);
    console.log('Table exists:', !!table);
    if (btn) {
        console.log('Button text:', btn.textContent);
        console.log('Button dataset:', btn.dataset);
        console.log('Button onclick:', btn.onclick);
    }
    if (table) {
        console.log('Table rows:', table.querySelectorAll('tbody tr').length);
    }
    console.log('==================');
};
