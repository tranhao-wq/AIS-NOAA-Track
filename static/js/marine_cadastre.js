// Marine Cadastre Map Functions

// Load Marine Cadastre Map
async function loadMarineCadastreMap() {
    try {
        // Kiểm tra xem iframe đã tồn tại chưa
        const existingIframe = document.querySelector('#marine-map iframe');
        if (existingIframe) {
            // Nếu đã có iframe, chỉ cần làm mới nó
            existingIframe.src = existingIframe.src;
            return;
        }
        
        document.getElementById('marine-map').innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ Marine Cadastre...</div>';
        
        // Tạo iframe mới
        setTimeout(() => {
            const iframe = document.createElement('iframe');
            iframe.src = 'https://marinecadastre.gov/nationalviewer/';
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.onload = () => {
                // Thêm thông báo khi iframe đã tải xong
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
                notification.textContent = 'Bản đồ Marine Cadastre đã được tải thành công!';
                
                document.getElementById('marine-map').appendChild(notification);
                
                // Tự động ẩn thông báo sau 3 giây
                setTimeout(() => {
                    notification.style.opacity = '0';
                    notification.style.transition = 'opacity 0.5s';
                    setTimeout(() => notification.remove(), 500);
                }, 3000);
            };
            
            // Xóa nội dung cũ và thêm iframe
            document.getElementById('marine-map').innerHTML = '';
            document.getElementById('marine-map').appendChild(iframe);
        }, 500);
    } catch (error) {
        document.getElementById('marine-map').innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi khi tải bản đồ: ${error.message}</div>`;
    }
}