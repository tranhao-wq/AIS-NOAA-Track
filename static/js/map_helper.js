// Helper functions for map display

function trustMap() {
    // Find all map iframes and make them trusted
    const mapIframes = document.querySelectorAll('.folium-map iframe');
    mapIframes.forEach(iframe => {
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
        iframe.setAttribute('src', iframe.getAttribute('src'));
    });
    
    console.log('Map trusted successfully');
}

// Auto-run when loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the map to load
    setTimeout(trustMap, 1000);
});