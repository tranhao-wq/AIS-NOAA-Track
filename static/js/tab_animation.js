// Tab animation functionality

// Enhanced tab switching with animation
function enhancedSwitchTab(tabId) {
    // Hide all tab contents with fade out effect
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.opacity = '0';
        tab.style.transition = 'opacity 0.3s';
        
        setTimeout(() => {
            tab.classList.remove('active');
            tab.style.opacity = '1';
        }, 300);
    });
    
    // Deactivate all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content with fade in effect
    setTimeout(() => {
        const selectedTab = document.getElementById(`tab-content-${tabId}`);
        selectedTab.classList.add('active');
        selectedTab.style.opacity = '0';
        
        setTimeout(() => {
            selectedTab.style.opacity = '1';
        }, 50);
        
        document.getElementById(`tab-${tabId}`).classList.add('active');
        
        // Add highlight effect to the tab button
        const activeButton = document.getElementById(`tab-${tabId}`);
        activeButton.style.transform = 'scale(1.05)';
        activeButton.style.transition = 'transform 0.3s';
        
        setTimeout(() => {
            activeButton.style.transform = 'scale(1)';
        }, 300);
    }, 300);
    
    // Save the active tab in session storage
    sessionStorage.setItem('activeTab', tabId);
}

// Override the original switchTab function
window.originalSwitchTab = window.switchTab;
window.switchTab = enhancedSwitchTab;

// Restore the active tab on page load
document.addEventListener('DOMContentLoaded', function() {
    const activeTab = sessionStorage.getItem('activeTab');
    if (activeTab) {
        enhancedSwitchTab(activeTab);
    }
});