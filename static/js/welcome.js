// Welcome message functionality

// Show welcome message with new features
function showWelcomeMessage() {
    setTimeout(() => {
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'welcome-message';
        welcomeMessage.innerHTML = `
            <div class="welcome-header">
                <h3>🚢 Chào mừng đến với AIS Marine Traffic Analyzer!</h3>
                <button onclick="this.parentNode.parentNode.remove()" class="close-btn">&times;</button>
            </div>
            <div class="welcome-content">
                <p>Ứng dụng đã được cập nhật với các tính năng mới:</p>
                <ul>
                    <li><strong>Tích hợp Marine Cadastre:</strong> Xem bản đồ trực tiếp từ marinecadastre.gov</li>
                    <li><strong>Phân tích rủi ro:</strong> Dự đoán và phân tích các hành trình có rủi ro cao</li>
                    <li><strong>Bản đồ rủi ro:</strong> Hiển thị trực quan các khu vực có nguy cơ cao</li>
                    <li><strong>Khai phá dữ liệu ẩn:</strong> Phát hiện các mẫu ẩn trong dữ liệu AIS</li>
                </ul>
                <p>Hãy khám phá các tab mới để trải nghiệm các tính năng này!</p>
            </div>
        `;
        document.body.appendChild(welcomeMessage);
        
        // Add CSS for welcome message
        const style = document.createElement('style');
        style.textContent = `
            .welcome-message {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border-radius: 10px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 600px;
                z-index: 1000;
                animation: fadeIn 0.5s;
            }
            
            .welcome-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: linear-gradient(45deg, #007bff, #0056b3);
                color: white;
                border-radius: 10px 10px 0 0;
            }
            
            .welcome-header h3 {
                margin: 0;
            }
            
            .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
            }
            
            .welcome-content {
                padding: 20px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }, 1000);
}

// Call this function when the page loads
document.addEventListener('DOMContentLoaded', showWelcomeMessage);