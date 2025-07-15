// Risk Analysis JavaScript Functions

// Analyze risky routes
async function analyzeRiskyRoutes() {
    try {
        const riskThreshold = document.getElementById('risk-threshold').value;
        const riskTypes = Array.from(document.getElementById('risk-type').selectedOptions).map(o => o.value);
        
        document.getElementById('risk-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang phân tích hành trình rủi ro...</div>';
        
        // Bước 1: Tính toán điểm rủi ro
        const calcResponse = await fetch('/calculate-risk-scores');
        
        if (!calcResponse.ok) {
            const error = await calcResponse.json();
            throw new Error(error.detail || 'Failed to calculate risk scores');
        }
        
        const riskStats = await calcResponse.json();
        
        // Bước 2: Xác định các hành trình rủi ro
        const routesResponse = await fetch('/identify-risky-routes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({risk_threshold: parseInt(riskThreshold)})
        });
        
        if (!routesResponse.ok) {
            const error = await routesResponse.json();
            throw new Error(error.detail || 'Failed to identify risky routes');
        }
        
        const result = await routesResponse.json();
        const riskyRoutes = result.risky_routes;
        
        // Tạo HTML
        let html = `<h4>Đã phát hiện ${riskyRoutes.length} hành trình rủi ro</h4>`;
        
        // Thêm thống kê rủi ro
        html += `
        <div class="risk-stats">
            <div class="risk-stat-card">
                <div class="stat-number">${riskStats.high_risk}</div>
                <div class="stat-label">Rủi ro cao</div>
            </div>
            <div class="risk-stat-card">
                <div class="stat-number">${riskStats.medium_risk}</div>
                <div class="stat-label">Rủi ro trung bình</div>
            </div>
            <div class="risk-stat-card">
                <div class="stat-number">${riskStats.low_risk}</div>
                <div class="stat-label">Rủi ro thấp</div>
            </div>
            <div class="risk-stat-card">
                <div class="stat-number">${riskStats.avg_risk_score.toFixed(1)}</div>
                <div class="stat-label">Điểm rủi ro TB</div>
            </div>
        </div>`;
        
        if (riskyRoutes.length > 0) {
            html += '<div class="risky-routes-container">';
            
            for (const route of riskyRoutes) {
                html += `
                <div class="risky-route-card">
                    <div class="risk-score" style="background: ${getRiskColor(route.riskScore)}">${route.riskScore}</div>
                    <div class="route-details">
                        <h5>${route.vesselName} (${route.vesselType})</h5>
                        <p><strong>MMSI:</strong> ${route.mmsi}</p>
                        <p><strong>Mô tả:</strong> ${route.description}</p>
                        <div class="risk-factors">
                            <div class="risk-factor" style="width: ${route.riskFactors.collision}%">Va chạm: ${route.riskFactors.collision}</div>
                            <div class="risk-factor" style="width: ${route.riskFactors.weather}%">Thời tiết: ${route.riskFactors.weather}</div>
                            <div class="risk-factor" style="width: ${route.riskFactors.route}%">Lệch tuyến: ${route.riskFactors.route}</div>
                            <div class="risk-factor" style="width: ${route.riskFactors.speed}%">Tốc độ: ${route.riskFactors.speed}</div>
                            <div class="risk-factor" style="width: ${route.riskFactors.navigation}%">Chướng ngại: ${route.riskFactors.navigation}</div>
                        </div>
                    </div>
                </div>`;
            }
            
            html += '</div>';
        } else {
            html += '<p>Không tìm thấy hành trình rủi ro nào với ngưỡng đã chọn.</p>';
        }
        
        document.getElementById('risk-result').innerHTML = html;
    } catch (error) {
        document.getElementById('risk-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
    }
}

// Show risk map
async function showRiskMap() {
    const riskMap = document.getElementById('risk-map');
    
    if (riskMap.style.display === 'none') {
        riskMap.style.display = 'block';
        riskMap.innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ rủi ro...</div>';
        
        try {
            const response = await fetch('/risk-map');
            const mapHtml = await response.text();
            riskMap.innerHTML = mapHtml;
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

// CSS for risk analysis
document.addEventListener('DOMContentLoaded', function() {
    // Add CSS for risk analysis
    const style = document.createElement('style');
    style.textContent = `
    .risk-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin: 20px 0;
    }
    
    .risk-stat-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        flex: 1;
        min-width: 100px;
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        color: #007bff;
    }
    
    .stat-label {
        margin-top: 5px;
        color: #6c757d;
    }
    `;
    document.head.appendChild(style);
    
    // Update risk threshold value display
    const riskThreshold = document.getElementById('risk-threshold');
    const riskThresholdValue = document.getElementById('risk-threshold-value');
    
    if (riskThreshold && riskThresholdValue) {
        riskThreshold.addEventListener('input', function() {
            riskThresholdValue.textContent = this.value;
        });
    }
});