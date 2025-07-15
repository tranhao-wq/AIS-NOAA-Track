// Dashboard functionality

// Load all analytics data for the dashboard
async function loadDashboard() {
    try {
        document.getElementById('dashboard-container').innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải dữ liệu phân tích...</div>';
        
        // Tải dữ liệu từ các API endpoint
        const [correlationsResponse, temporalResponse, groupsResponse] = await Promise.all([
            fetch('/analyze-correlations'),
            fetch('/analyze-temporal-patterns'),
            fetch('/detect-vessel-groups')
        ]);
        
        // Kiểm tra kết quả
        if (!correlationsResponse.ok || !temporalResponse.ok || !groupsResponse.ok) {
            throw new Error('Không thể tải dữ liệu phân tích');
        }
        
        // Xử lý dữ liệu
        const correlations = await correlationsResponse.json();
        const temporalPatterns = await temporalResponse.json();
        const vesselGroups = await groupsResponse.json();
        
        // Tạo dashboard
        let html = `
            <div class="dashboard-header">
                <h3>Bảng điều khiển phân tích</h3>
                <p>Tổng hợp các phân tích nâng cao từ dữ liệu AIS</p>
            </div>
            
            <div class="dashboard-grid">
                <!-- Phân tích tương quan -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>Phân tích tương quan</h4>
                    </div>
                    <div class="card-body">
                        ${renderCorrelations(correlations)}
                    </div>
                </div>
                
                <!-- Phân tích thời gian -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>Phân tích theo thời gian</h4>
                    </div>
                    <div class="card-body">
                        ${renderTemporalPatterns(temporalPatterns)}
                    </div>
                </div>
                
                <!-- Nhóm tàu -->
                <div class="dashboard-card">
                    <div class="card-header">
                        <h4>Nhóm tàu di chuyển cùng nhau</h4>
                    </div>
                    <div class="card-body">
                        ${renderVesselGroups(vesselGroups)}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('dashboard-container').innerHTML = html;
    } catch (error) {
        document.getElementById('dashboard-container').innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi: ${error.message}</div>`;
    }
}

// Render correlations data
function renderCorrelations(data) {
    if (data.error) {
        return `<div class="error-message">${data.error}</div>`;
    }
    
    let html = '';
    
    // Hiển thị biểu đồ tương quan
    if (data.chart) {
        html += `<div class="chart-container"><img src="data:image/png;base64,${data.chart}" alt="Correlation Chart"></div>`;
    }
    
    // Hiển thị danh sách tương quan mạnh
    if (data.correlations && data.correlations.length > 0) {
        html += '<h5>Tương quan mạnh nhất:</h5><ul class="correlation-list">';
        
        data.correlations.slice(0, 5).forEach(corr => {
            const corrClass = corr.correlation > 0 ? 'positive' : 'negative';
            html += `
                <li class="${corrClass}">
                    <span class="var-names">${corr.variable1} & ${corr.variable2}</span>
                    <span class="corr-value">${corr.correlation.toFixed(2)}</span>
                    <span class="corr-desc">(${corr.direction}, ${corr.strength})</span>
                </li>
            `;
        });
        
        html += '</ul>';
    } else {
        html += '<p>Không tìm thấy tương quan đáng kể nào.</p>';
    }
    
    return html;
}

// Render temporal patterns data
function renderTemporalPatterns(data) {
    if (data.error) {
        return `<div class="error-message">${data.error}</div>`;
    }
    
    let html = '';
    
    // Hiển thị biểu đồ phân tích thời gian
    if (data.chart) {
        html += `<div class="chart-container"><img src="data:image/png;base64,${data.chart}" alt="Temporal Patterns Chart"></div>`;
    }
    
    // Hiển thị các mẫu thời gian
    if (data.temporal_patterns && data.temporal_patterns.length > 0) {
        html += '<h5>Mẫu thời gian phát hiện được:</h5><ul class="pattern-list">';
        
        data.temporal_patterns.forEach(pattern => {
            html += `<li>${pattern.description}</li>`;
        });
        
        html += '</ul>';
    } else {
        html += '<p>Không tìm thấy mẫu thời gian đáng kể nào.</p>';
    }
    
    return html;
}

// Render vessel groups data
function renderVesselGroups(data) {
    if (data.error) {
        return `<div class="error-message">${data.error}</div>`;
    }
    
    let html = '';
    
    // Hiển thị thông tin tổng quan về nhóm tàu
    html += `
        <div class="groups-summary">
            <div class="summary-item">
                <div class="summary-value">${data.total_groups}</div>
                <div class="summary-label">Nhóm tàu</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">${data.total_vessels_in_groups}</div>
                <div class="summary-label">Tổng số tàu</div>
            </div>
        </div>
    `;
    
    // Hiển thị danh sách các nhóm tàu
    if (data.vessel_groups && data.vessel_groups.length > 0) {
        html += '<h5>Các nhóm tàu lớn nhất:</h5><div class="groups-list">';
        
        data.vessel_groups.slice(0, 3).forEach((group, index) => {
            html += `
                <div class="group-card">
                    <div class="group-header">Nhóm ${index + 1}</div>
                    <div class="group-details">
                        <p><strong>Số tàu:</strong> ${group.vessel_count}</p>
                        <p><strong>Khoảng cách TB:</strong> ${group.avg_distance_km} km</p>
                        <p><strong>Loại tàu:</strong> ${group.vessel_types.join(', ') || 'Không xác định'}</p>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        // Thêm nút để xem bản đồ nhóm tàu
        html += `
            <div class="view-map-button">
                <button onclick="showVesselGroupsMap()" style="background: linear-gradient(45deg, #20c997, #0ca678);">
                    Xem bản đồ nhóm tàu
                </button>
            </div>
        `;
    } else {
        html += '<p>Không tìm thấy nhóm tàu nào.</p>';
    }
    
    return html;
}

// Show vessel groups map
async function showVesselGroupsMap() {
    try {
        const mapContainer = document.getElementById('vessel-groups-map');
        
        if (!mapContainer) {
            // Tạo container cho bản đồ nếu chưa có
            const container = document.createElement('div');
            container.id = 'vessel-groups-map';
            container.className = 'vessel-groups-map';
            container.innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ nhóm tàu...</div>';
            
            // Thêm vào sau dashboard container
            document.getElementById('dashboard-container').appendChild(container);
        } else {
            mapContainer.innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ nhóm tàu...</div>';
            mapContainer.style.display = 'block';
        }
        
        // Tải dữ liệu bản đồ
        const response = await fetch('/detect-vessel-groups');
        
        if (!response.ok) {
            throw new Error('Không thể tải dữ liệu nhóm tàu');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Hiển thị bản đồ
        document.getElementById('vessel-groups-map').innerHTML = data.map_html || '<div class="error-message">Không có dữ liệu bản đồ</div>';
        
    } catch (error) {
        if (document.getElementById('vessel-groups-map')) {
            document.getElementById('vessel-groups-map').innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi: ${error.message}</div>`;
        }
    }
}

// Add CSS for dashboard
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .dashboard-header {
            margin-bottom: 20px;
            text-align: center;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .dashboard-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .card-header {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            padding: 15px;
        }
        
        .card-header h4 {
            margin: 0;
        }
        
        .card-body {
            padding: 15px;
        }
        
        .chart-container {
            margin: 10px 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            border-radius: 5px;
        }
        
        .correlation-list, .pattern-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .correlation-list li, .pattern-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .correlation-list li:last-child, .pattern-list li:last-child {
            border-bottom: none;
        }
        
        .correlation-list .positive {
            color: #28a745;
        }
        
        .correlation-list .negative {
            color: #dc3545;
        }
        
        .var-names {
            font-weight: bold;
        }
        
        .corr-value {
            margin-left: 10px;
        }
        
        .corr-desc {
            color: #6c757d;
            font-size: 0.9em;
            margin-left: 5px;
        }
        
        .groups-summary {
            display: flex;
            justify-content: space-around;
            margin-bottom: 15px;
        }
        
        .summary-item {
            text-align: center;
        }
        
        .summary-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        
        .summary-label {
            color: #6c757d;
        }
        
        .groups-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .group-card {
            border: 1px solid #dee2e6;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .group-header {
            background: #f8f9fa;
            padding: 8px 12px;
            font-weight: bold;
            border-bottom: 1px solid #dee2e6;
        }
        
        .group-details {
            padding: 10px;
        }
        
        .group-details p {
            margin: 5px 0;
        }
        
        .view-map-button {
            margin-top: 15px;
            text-align: center;
        }
        
        .vessel-groups-map {
            margin-top: 20px;
            height: 500px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #dee2e6;
        }
        
        .error-message {
            color: #dc3545;
            padding: 10px;
            background: #f8d7da;
            border-radius: 5px;
            margin: 10px 0;
        }
    `;
    document.head.appendChild(style);
});