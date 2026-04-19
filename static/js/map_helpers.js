// Leaflet map helper
function initMap(containerId, lat, lng) {
    const map = L.map(containerId).setView([lat, lng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    return map;
}