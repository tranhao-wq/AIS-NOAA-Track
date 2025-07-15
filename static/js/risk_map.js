// Risk Map JavaScript Functions

// Show risk map using Leaflet
async function showRiskMap() {
    const riskMap = document.getElementById('risk-map');
    
    if (riskMap.style.display === 'none') {
        riskMap.style.display = 'block';
        riskMap.innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ rủi ro...</div>';
        
        try {
            // Tải dữ liệu bản đồ rủi ro
            const response = await fetch('/risk-map');
            const mapHtml = await response.text();
            
            // Hiển thị bản đồ
            riskMap.innerHTML = mapHtml;
            
            // Thêm thông báo thành công
            const notification = document.createElement('div');
            notification.style.position = 'absolute';
            notification.style.top = '10px';
            notification.style.left = '50%';
            notification.style.transform = 'translateX(-50%)';
            notification.style.background = 'rgba(40, 167, 69, 0.9)';
            notification.style.color = 'white';
            notification.style.padding = '10px 20px';
            notification.style.borderRadius = '5px';
            notification.style.fontWeight = 'bold';
            notification.style.zIndex = '1000';
            notification.textContent = 'Bản đồ rủi ro đã được tải thành công!';
            
            riskMap.appendChild(notification);
            
            // Tự động ẩn thông báo sau 3 giây
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.5s';
                setTimeout(() => notification.remove(), 500);
            }, 3000);
        } catch (error) {
            riskMap.innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi khi tải bản đồ: ${error.message}</div>`;
        }
    } else {
        riskMap.style.display = 'none';
    }
}

// Helper function to get risk color
function getRiskColor(score) {
    if (score >= 80) return '#dc3545';
    if (score >= 60) return '#fd7e14';
    return '#28a745';
}