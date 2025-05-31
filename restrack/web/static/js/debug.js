// Debug script for htmx requests
document.addEventListener('DOMContentLoaded', function () {
    console.log('DEBUG: DOMContentLoaded fired');

    // Check if elements exist
    const subscriptionManager = document.getElementById('subscription-manager');
    const copyManager = document.getElementById('copy-manager');
    const worklistSelector = document.getElementById('worklist-selector');

    console.log('DEBUG: Elements found:');
    console.log('- subscription-manager:', subscriptionManager);
    console.log('- copy-manager:', copyManager);
    console.log('- worklist-selector:', worklistSelector);

    // Listen for htmx requests
    document.body.addEventListener('htmx:beforeRequest', function (event) {
        console.log('HTMX Request:', event.detail.path, event.detail);
    });

    document.body.addEventListener('htmx:afterRequest', function (event) {
        console.log('HTMX Response:', event.detail.path, event.detail);

        // Check for empty responses
        if (event.detail.xhr.responseText.trim() === '') {
            console.warn('HTMX Empty Response:', event.detail.path, event.detail);
        }
    });

    document.body.addEventListener('htmx:responseError', function (event) {
        console.error('HTMX Error:', event.detail.path, event.detail);
    });

    // Manually trigger the loading of components if they're empty
    setTimeout(function () {
        console.log('DEBUG: Checking if components need manual loading...');

        const subscriptionManager = document.getElementById('subscription-manager');
        const copyManager = document.getElementById('copy-manager');

        if (subscriptionManager) {
            console.log('DEBUG: subscription-manager innerHTML:', subscriptionManager.innerHTML.trim());
            if (!subscriptionManager.innerHTML.trim()) {
                console.log('Manually loading subscription manager...');
                htmx.ajax('GET', '/worklists/subscription-manager', { target: '#subscription-manager' });
            }
        } else {
            console.warn('DEBUG: subscription-manager element not found');
        }

        if (copyManager) {
            console.log('DEBUG: copy-manager innerHTML:', copyManager.innerHTML.trim());
            if (!copyManager.innerHTML.trim()) {
                console.log('Manually loading copy manager...');
                htmx.ajax('GET', '/worklists/copy-manager', { target: '#copy-manager' });
            }
        } else {
            console.warn('DEBUG: copy-manager element not found');
        }
    }, 1000);

    // Also try loading on tab switch
    document.addEventListener('shown.bs.tab', function (event) {
        console.log('DEBUG: Tab switched to:', event.target.getAttribute('data-bs-target'));
        if (event.target.getAttribute('data-bs-target') === '#manage') {
            console.log('DEBUG: Manage tab activated, loading components...');
            setTimeout(function () {
                if (document.getElementById('subscription-manager') && !document.getElementById('subscription-manager').innerHTML.trim()) {
                    htmx.ajax('GET', '/worklists/subscription-manager', { target: '#subscription-manager' });
                }
                if (document.getElementById('copy-manager') && !document.getElementById('copy-manager').innerHTML.trim()) {
                    htmx.ajax('GET', '/worklists/copy-manager', { target: '#copy-manager' });
                }
            }, 100);
        }
    });
});
