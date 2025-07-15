import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import io
import base64

def detect_vessel_patterns(df):
    """Phát hiện mẫu di chuyển bất thường của tàu"""
    try:
        # Tìm cột tọa độ
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        
        if not lat_col or not lon_col:
            return {"error": "Không tìm thấy cột tọa độ"}
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[lat_col, lon_col])
        df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
        df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
        
        if len(df_clean) < 10:
            return {"error": "Không đủ dữ liệu để phân tích"}
        
        # Chuẩn hóa dữ liệu
        coords = df_clean[[lat_col, lon_col]].values
        coords_scaled = StandardScaler().fit_transform(coords)
        
        # Phát hiện cụm bằng DBSCAN
        db = DBSCAN(eps=0.3, min_samples=5).fit(coords_scaled)
        labels = db.labels_
        
        # Số lượng cụm (không tính nhiễu)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Thêm nhãn cụm vào dữ liệu
        df_clean['cluster'] = labels
        
        # Tính toán trung tâm của các cụm
        clusters = []
        for i in range(n_clusters):
            cluster_points = df_clean[df_clean['cluster'] == i]
            center_lat = cluster_points[lat_col].mean()
            center_lon = cluster_points[lon_col].mean()
            size = len(cluster_points)
            clusters.append({
                'id': i,
                'center': [center_lat, center_lon],
                'size': size,
                'points': len(cluster_points)
            })
        
        # Tính tỷ lệ điểm nhiễu
        noise_ratio = np.sum(labels == -1) / len(labels)
        
        return {
            "clusters": clusters,
            "n_clusters": n_clusters,
            "noise_ratio": noise_ratio,
            "total_points": len(df_clean)
        }
    except Exception as e:
        return {"error": str(e)}

def predict_vessel_density(df):
    """Dự đoán mật độ tàu thuyền trong khu vực"""
    try:
        # Tìm cột tọa độ
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        
        if not lat_col or not lon_col:
            return {"error": "Không tìm thấy cột tọa độ"}
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[lat_col, lon_col])
        df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
        df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
        
        if len(df_clean) < 10:
            return {"error": "Không đủ dữ liệu để phân tích"}
        
        # Tạo lưới mật độ
        lat_min, lat_max = df_clean[lat_col].min(), df_clean[lat_col].max()
        lon_min, lon_max = df_clean[lon_col].min(), df_clean[lon_col].max()
        
        # Tạo lưới 10x10
        lat_bins = np.linspace(lat_min, lat_max, 11)
        lon_bins = np.linspace(lon_min, lon_max, 11)
        
        # Đếm số lượng tàu trong mỗi ô lưới
        density_grid = np.zeros((10, 10))
        for i in range(10):
            for j in range(10):
                density_grid[i, j] = np.sum(
                    (df_clean[lat_col] >= lat_bins[i]) & 
                    (df_clean[lat_col] < lat_bins[i+1]) & 
                    (df_clean[lon_col] >= lon_bins[j]) & 
                    (df_clean[lon_col] < lon_bins[j+1])
                )
        
        # Tạo dữ liệu heatmap
        heatmap_data = []
        for i in range(10):
            for j in range(10):
                if density_grid[i, j] > 0:
                    heatmap_data.append([
                        (lat_bins[i] + lat_bins[i+1]) / 2,
                        (lon_bins[j] + lon_bins[j+1]) / 2,
                        float(density_grid[i, j])
                    ])
        
        # Tìm các khu vực có mật độ cao
        high_density_areas = []
        threshold = np.percentile(density_grid[density_grid > 0], 75)  # Ngưỡng 75%
        for i in range(10):
            for j in range(10):
                if density_grid[i, j] > threshold:
                    high_density_areas.append({
                        'center': [
                            (lat_bins[i] + lat_bins[i+1]) / 2,
                            (lon_bins[j] + lon_bins[j+1]) / 2
                        ],
                        'density': float(density_grid[i, j]),
                        'bounds': [
                            [lat_bins[i], lon_bins[j]],
                            [lat_bins[i+1], lon_bins[j+1]]
                        ]
                    })
        
        return {
            "heatmap_data": heatmap_data,
            "high_density_areas": high_density_areas,
            "max_density": float(np.max(density_grid)),
            "avg_density": float(np.mean(density_grid[density_grid > 0]))
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_vessel_types(df):
    """Phân tích chi tiết theo loại tàu"""
    try:
        # Tìm cột loại tàu
        vessel_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        if not vessel_col:
            return {"error": "Không tìm thấy cột loại tàu"}
        
        # Đếm số lượng theo loại tàu
        vessel_counts = df[vessel_col].value_counts().to_dict()
        
        # Tìm cột tốc độ
        speed_col = next((col for col in ['SOG', 'Speed', 'speed'] if col in df.columns), None)
        
        speed_stats = {}
        if speed_col:
            # Thống kê tốc độ theo loại tàu
            for vessel_type in vessel_counts.keys():
                vessel_data = df[df[vessel_col] == vessel_type]
                if len(vessel_data) > 0:
                    speed_stats[vessel_type] = {
                        'avg_speed': float(vessel_data[speed_col].mean()),
                        'max_speed': float(vessel_data[speed_col].max()),
                        'min_speed': float(vessel_data[speed_col].min())
                    }
        
        # Tạo biểu đồ phân bố loại tàu
        plt.figure(figsize=(10, 6))
        plt.bar(vessel_counts.keys(), vessel_counts.values())
        plt.title('Phân bố loại tàu')
        plt.xlabel('Loại tàu')
        plt.ylabel('Số lượng')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Chuyển biểu đồ thành base64 để hiển thị trên web
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return {
            "vessel_counts": vessel_counts,
            "speed_stats": speed_stats,
            "chart": chart
        }
    except Exception as e:
        return {"error": str(e)}

def generate_advanced_map(df):
    """Tạo bản đồ nâng cao với nhiều lớp dữ liệu sử dụng Leaflet"""
    try:
        # Tìm cột tọa độ
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        
        if not lat_col or not lon_col:
            return "<div>Không tìm thấy cột tọa độ</div>"
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[lat_col, lon_col])
        df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
        df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
        
        if len(df_clean) < 1:
            return "<div>Không đủ dữ liệu để tạo bản đồ</div>"
        
        # Tính toán trung tâm bản đồ
        center_lat = df_clean[lat_col].mean()
        center_lon = df_clean[lon_col].mean()
        
        # Tạo bản đồ sử dụng Leaflet
        map_html = f'''
        <div id="advanced-vessel-map" style="height: 600px; width: 100%; border-radius: 10px;"></div>
        <script>
            // Kiểm tra xem Leaflet đã được tải chưa
            if (typeof L === 'undefined') {{            
                // Tải Leaflet CSS và JavaScript
                var leafletCSS = document.createElement('link');
                leafletCSS.rel = 'stylesheet';
                leafletCSS.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css';
                document.head.appendChild(leafletCSS);
                
                var leafletJS = document.createElement('script');
                leafletJS.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
                document.head.appendChild(leafletJS);
                
                // Tải Leaflet.heat cho bản đồ nhiệt
                var leafletHeatJS = document.createElement('script');
                leafletHeatJS.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
                document.head.appendChild(leafletHeatJS);
                
                // Tải Leaflet.markercluster
                var markerClusterCSS = document.createElement('link');
                markerClusterCSS.rel = 'stylesheet';
                markerClusterCSS.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css';
                document.head.appendChild(markerClusterCSS);
                
                var markerClusterDefaultCSS = document.createElement('link');
                markerClusterDefaultCSS.rel = 'stylesheet';
                markerClusterDefaultCSS.href = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css';
                document.head.appendChild(markerClusterDefaultCSS);
                
                var markerClusterJS = document.createElement('script');
                markerClusterJS.src = 'https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js';
                document.head.appendChild(markerClusterJS);
                
                // Đợi Leaflet và các plugin tải xong
                var checkInterval = setInterval(function() {{
                    if (typeof L !== 'undefined' && 
                        typeof L.markerClusterGroup !== 'undefined' && 
                        typeof L.heatLayer !== 'undefined') {{
                        clearInterval(checkInterval);
                        initAdvancedMap();
                    }}
                }}, 100);
            }} else {{
                // Leaflet đã được tải, khởi tạo bản đồ ngay lập tức
                initAdvancedMap();
            }}
            
            function initAdvancedMap() {{
                // Tạo bản đồ
                var map = L.map('advanced-vessel-map').setView([{center_lat}, {center_lon}], 8);
                
                // Thêm lớp bản đồ nền
                var baseLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Màu sắc cho các loại tàu
                var vesselColors = {{
                    'Cargo': '#3388ff',
                    'Tanker': '#dc3545',
                    'Passenger': '#28a745',
                    'Fishing': '#fd7e14',
                    'Tug': '#6f42c1',
                    'Military': '#000000',
                    'Sailing': '#e83e8c',
                    'Unknown': '#6c757d'
                }};
                
                // Tạo các lớp cho từng loại tàu
                var vesselLayers = {{}};                
                var allMarkers = [];
                var heatData = [];
        '''
        
        # Tìm cột loại tàu
        vessel_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        # Giới hạn số điểm để tránh quá tải
        max_points = min(1000, len(df_clean))
        df_sample = df_clean.sample(n=max_points) if len(df_clean) > max_points else df_clean
        
        # Tạo các lớp cho từng loại tàu
        vessel_types = []
        if vessel_col:
            vessel_types = df_clean[vessel_col].unique()
            vessel_types = [str(vt) for vt in vessel_types if pd.notna(vt)]
            
            # Thêm mã JavaScript để tạo các lớp
            for vessel_type in vessel_types:
                map_html += f'''
                vesselLayers['{vessel_type}'] = L.layerGroup();
                '''
        
        # Thêm các điểm vào bản đồ
        map_html += '''
                // Tạo cụm marker
                var markerCluster = L.markerClusterGroup();
                
                // Dữ liệu điểm
                var points = [
        '''
        
        # Thêm các điểm vào danh sách
        points_data = []
        for _, row in df_sample.iterrows():
            vessel_type = str(row.get(vessel_col, 'Unknown')) if vessel_col else 'Unknown'
            vessel_type = vessel_type.replace("'", "\\'")
            
            # Tạo popup text
            popup_text = f"Vị trí: {row[lat_col]:.4f}, {row[lon_col]:.4f}"
            if vessel_col:
                popup_text += f"<br>Loại tàu: {vessel_type}"
            
            # Thêm thông tin khác
            for col in ['MMSI', 'VesselName', 'SOG', 'COG', 'BaseDateTime']:
                if col in row and pd.notna(row[col]):
                    popup_text += f"<br>{col}: {row[col]}"
            
            # Thêm điểm vào danh sách
            points_data.append(f"[{row[lat_col]}, {row[lon_col]}, '{vessel_type}', '{popup_text}']")
        
        # Thêm các điểm vào mã JavaScript
        map_html += ',\n                    '.join(points_data)
        
        # Hoàn thành mã JavaScript
        map_html += '''
                ];
                
                // Thêm các điểm vào bản đồ
                points.forEach(function(point) {
                    var lat = point[0];
                    var lon = point[1];
                    var type = point[2];
                    var popupText = point[3];
                    
                    var color = vesselColors[type] || vesselColors['Unknown'];
                    
                    var marker = L.circleMarker([lat, lon], {
                        radius: 5,
                        color: color,
                        fillColor: color,
                        fillOpacity: 0.7,
                        weight: 2
                    }).bindPopup(popupText);
                    
                    // Thêm vào cụm marker
                    markerCluster.addLayer(marker);
                    
                    // Thêm vào lớp tương ứng
                    if (vesselLayers[type]) {
                        vesselLayers[type].addLayer(marker);
                    }
                    
                    // Thêm vào danh sách tất cả marker
                    allMarkers.push(marker);
                    
                    // Thêm vào dữ liệu heatmap
                    heatData.push([lat, lon, 0.5]);
                });
                
                // Thêm cụm marker vào bản đồ
                map.addLayer(markerCluster);
                
                // Tạo heatmap
                var heatLayer = L.heatLayer(heatData, {
                    radius: 20,
                    blur: 15,
                    maxZoom: 10,
                    max: 1.0,
                    gradient: {0.4: 'blue', 0.65: 'yellow', 0.9: 'red'}
                });
                
                // Tạo các lớp cơ sở
                var baseLayers = {
                    "Bản đồ nền": baseLayer
                };
                
                // Tạo các lớp phủ
                var overlays = {
                    "Tất cả tàu": markerCluster,
                    "Bản đồ nhiệt": heatLayer
                };
                
                // Thêm các lớp loại tàu vào overlays
                for (var type in vesselLayers) {
                    overlays["Tàu " + type] = vesselLayers[type];
                }
                
                // Thêm điều khiển lớp
                L.control.layers(baseLayers, overlays).addTo(map);
                
                // Thêm chú thích
                var legend = L.control({position: 'bottomright'});
                legend.onAdd = function(map) {
                    var div = L.DomUtil.create('div', 'info legend');
                    div.style.backgroundColor = 'white';
                    div.style.padding = '10px';
                    div.style.borderRadius = '5px';
                    div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                    
                    div.innerHTML = '<h4 style="margin-top: 0;">🚢 Loại tàu</h4>';
                    
                    // Thêm các loại tàu vào chú thích
                    for (var type in vesselColors) {
                        if (type in vesselLayers || type === 'Unknown') {
                            div.innerHTML += 
                                '<div><span style="display:inline-block; width:15px; height:15px; border-radius:50%; background:' + 
                                vesselColors[type] + ';"></span> ' + type + '</div>';
                        }
                    }
                    
                    return div;
                };
                legend.addTo(map);
            }
        </script>
        '''
        
        return map_html
    except Exception as e:
        return f"<div>Lỗi khi tạo bản đồ: {str(e)}</div>"

def detect_anomalies(df):
    """Phát hiện dữ liệu bất thường"""
    try:
        # Tìm cột tốc độ
        speed_col = next((col for col in ['SOG', 'Speed', 'speed'] if col in df.columns), None)
        
        if not speed_col:
            return {"error": "Không tìm thấy cột tốc độ"}
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[speed_col])
        
        if len(df_clean) < 10:
            return {"error": "Không đủ dữ liệu để phân tích"}
        
        # Tính ngưỡng bất thường (phương pháp IQR)
        Q1 = df_clean[speed_col].quantile(0.25)
        Q3 = df_clean[speed_col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Phát hiện bất thường
        anomalies = df_clean[(df_clean[speed_col] < lower_bound) | (df_clean[speed_col] > upper_bound)]
        
        # Thống kê
        anomaly_stats = {
            "total_anomalies": len(anomalies),
            "anomaly_ratio": len(anomalies) / len(df_clean),
            "speed_threshold": {
                "lower": float(lower_bound),
                "upper": float(upper_bound)
            }
        }
        
        # Tìm cột loại tàu
        vessel_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        # Phân tích bất thường theo loại tàu
        if vessel_col:
            anomaly_by_type = anomalies[vessel_col].value_counts().to_dict()
            anomaly_stats["anomaly_by_type"] = anomaly_by_type
        
        return anomaly_stats
    except Exception as e:
        return {"error": str(e)}

def analyze_correlations(df):
    """Phân tích tương quan giữa các biến"""
    try:
        # Tìm các cột số liệu
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # Loại bỏ các cột không có ý nghĩa cho phân tích tương quan
        exclude_cols = ['MMSI', 'IMO', 'VesselID']
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        if len(numeric_cols) < 2:
            return {"error": "Không đủ dữ liệu số để phân tích tương quan"}
        
        # Tính ma trận tương quan
        corr_df = df[numeric_cols].corr().round(2)
        
        # Chuyển ma trận tương quan thành danh sách các cặp tương quan
        correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                col1 = numeric_cols[i]
                col2 = numeric_cols[j]
                corr_value = corr_df.loc[col1, col2]
                
                # Chỉ lấy các tương quan mạnh (trị tuyệt đối > 0.3)
                if abs(corr_value) > 0.3:
                    correlations.append({
                        "variable1": col1,
                        "variable2": col2,
                        "correlation": float(corr_value),
                        "strength": "mạnh" if abs(corr_value) > 0.7 else "trung bình",
                        "direction": "thuận" if corr_value > 0 else "nghịch"
                    })
        
        # Sắp xếp theo độ mạnh của tương quan (giảm dần)
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        # Tạo biểu đồ tương quan
        plt.figure(figsize=(10, 8))
        plt.matshow(corr_df, fignum=1, cmap='coolwarm', vmin=-1, vmax=1)
        plt.colorbar()
        plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=90)
        plt.yticks(range(len(numeric_cols)), numeric_cols)
        
        # Thêm giá trị tương quan vào biểu đồ
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                plt.text(i, j, f"{corr_df.iloc[j, i]:.2f}", 
                         ha="center", va="center", 
                         color="white" if abs(corr_df.iloc[j, i]) > 0.5 else "black")
        
        plt.tight_layout()
        
        # Chuyển biểu đồ thành base64 để hiển thị trên web
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        correlation_chart = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return {
            "correlations": correlations,
            "total_correlations": len(correlations),
            "chart": correlation_chart
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_temporal_patterns(df):
    """Phân tích mẫu theo thời gian"""
    try:
        # Tìm cột thời gian
        time_col = next((col for col in ['BaseDateTime', 'DateTime', 'Timestamp', 'date_time'] if col in df.columns), None)
        
        if not time_col:
            return {"error": "Không tìm thấy cột thời gian"}
        
        # Chuyển đổi cột thời gian sang định dạng datetime
        df['parsed_time'] = pd.to_datetime(df[time_col], errors='coerce')
        df_time = df.dropna(subset=['parsed_time'])
        
        if len(df_time) < 10:
            return {"error": "Không đủ dữ liệu thời gian để phân tích"}
        
        # Thêm các cột thời gian
        df_time['hour'] = df_time['parsed_time'].dt.hour
        df_time['day_of_week'] = df_time['parsed_time'].dt.dayofweek
        df_time['day_name'] = df_time['parsed_time'].dt.day_name()
        df_time['month'] = df_time['parsed_time'].dt.month
        
        # Phân tích theo giờ trong ngày
        hourly_counts = df_time['hour'].value_counts().sort_index()
        
        # Tìm giờ cao điểm
        peak_hour = hourly_counts.idxmax()
        peak_count = hourly_counts.max()
        
        # Phân tích theo ngày trong tuần
        daily_counts = df_time['day_of_week'].value_counts().sort_index()
        day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        daily_data = {day_names[i]: int(daily_counts.get(i, 0)) for i in range(7)}
        
        # Tìm ngày bận rộn nhất
        busiest_day_idx = daily_counts.idxmax() if not daily_counts.empty else 0
        busiest_day = day_names[busiest_day_idx]
        busiest_day_count = daily_counts.max() if not daily_counts.empty else 0
        
        # Tạo biểu đồ phân bố theo giờ
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.bar(hourly_counts.index, hourly_counts.values, color='skyblue')
        plt.title('Phân bố theo giờ trong ngày')
        plt.xlabel('Giờ')
        plt.ylabel('Số lượng')
        plt.xticks(range(0, 24, 2))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Tạo biểu đồ phân bố theo ngày trong tuần
        plt.subplot(1, 2, 2)
        plt.bar(day_names, [daily_data.get(day, 0) for day in day_names], color='lightgreen')
        plt.title('Phân bố theo ngày trong tuần')
        plt.xlabel('Ngày')
        plt.ylabel('Số lượng')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Chuyển biểu đồ thành base64 để hiển thị trên web
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        time_chart = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        # Tím các mẫu thời gian đặc biệt
        temporal_patterns = [
            {
                "type": "peak_hour",
                "description": f"Giờ cao điểm là {peak_hour}h với {peak_count} tàu",
                "details": {
                    "hour": int(peak_hour),
                    "count": int(peak_count)
                }
            },
            {
                "type": "busiest_day",
                "description": f"Ngày bận rộn nhất là {busiest_day} với {busiest_day_count} tàu",
                "details": {
                    "day": busiest_day,
                    "count": int(busiest_day_count)
                }
            }
        ]
        
        # Tìm các khoảng thời gian có hoạt động bất thường
        # Tính trung bình và độ lệch chuẩn của số lượng theo giờ
        mean_hourly = hourly_counts.mean()
        std_hourly = hourly_counts.std()
        
        # Xác định các giờ có hoạt động bất thường (> mean + 1.5*std)
        anomaly_hours = hourly_counts[hourly_counts > (mean_hourly + 1.5 * std_hourly)]
        
        for hour, count in anomaly_hours.items():
            temporal_patterns.append({
                "type": "anomaly_hour",
                "description": f"Hoạt động bất thường cao vào lúc {hour}h với {count} tàu",
                "details": {
                    "hour": int(hour),
                    "count": int(count),
                    "mean": float(mean_hourly),
                    "std": float(std_hourly)
                }
            })
        
        return {
            "temporal_patterns": temporal_patterns,
            "hourly_distribution": {str(h): int(hourly_counts.get(h, 0)) for h in range(24)},
            "daily_distribution": daily_data,
            "chart": time_chart
        }
    except Exception as e:
        return {"error": str(e)}

def detect_vessel_groups(df):
    """Phát hiện các nhóm tàu di chuyển cùng nhau"""
    try:
        # Tìm các cột cần thiết
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        mmsi_col = next((col for col in ['MMSI', 'mmsi', 'VesselId'] if col in df.columns), None)
        time_col = next((col for col in ['BaseDateTime', 'DateTime', 'Timestamp', 'date_time'] if col in df.columns), None)
        
        if not all([lat_col, lon_col, mmsi_col]):
            return {"error": "Thiếu các cột dữ liệu cần thiết"}
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[lat_col, lon_col, mmsi_col])
        df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
        df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
        
        if len(df_clean) < 20:
            return {"error": "Không đủ dữ liệu để phát hiện nhóm tàu"}
        
        # Nếu có cột thời gian, sẽ phân tích theo thời gian
        if time_col and time_col in df_clean.columns:
            df_clean['parsed_time'] = pd.to_datetime(df_clean[time_col], errors='coerce')
            df_clean = df_clean.dropna(subset=['parsed_time'])
            
            # Lấy mẫu dữ liệu gần đây nhất (nếu quá lớn)
            if len(df_clean) > 1000:
                df_clean = df_clean.sort_values('parsed_time', ascending=False).head(1000)
        
        # Chuẩn hóa dữ liệu
        coords = df_clean[[lat_col, lon_col]].values
        coords_scaled = StandardScaler().fit_transform(coords)
        
        # Phát hiện cụm bằng DBSCAN
        db = DBSCAN(eps=0.1, min_samples=3).fit(coords_scaled)
        labels = db.labels_
        
        # Thêm nhãn cụm vào dữ liệu
        df_clean['cluster'] = labels
        
        # Số lượng cụm (không tính nhiễu)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        if n_clusters == 0:
            return {"error": "Không phát hiện được nhóm tàu nào"}
        
        # Phân tích các nhóm tàu
        vessel_groups = []
        
        for i in range(n_clusters):
            cluster_data = df_clean[df_clean['cluster'] == i]
            
            # Tính toán trung tâm của cụm
            center_lat = cluster_data[lat_col].mean()
            center_lon = cluster_data[lon_col].mean()
            
            # Đếm số lượng tàu duy nhất trong cụm
            unique_vessels = cluster_data[mmsi_col].nunique()
            
            # Xác định loại tàu trong cụm
            vessel_type_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df_clean.columns), None)
            vessel_types = []
            if vessel_type_col:
                vessel_types = cluster_data[vessel_type_col].unique().tolist()
                vessel_types = [str(vt) for vt in vessel_types if pd.notna(vt)]
            
            # Tính khoảng cách trung bình giữa các tàu trong cụm
            if len(cluster_data) > 1:
                from scipy.spatial.distance import pdist
                distances = pdist(cluster_data[[lat_col, lon_col]].values)
                avg_distance = float(np.mean(distances))
                # Chuyển đổi khoảng cách từ độ sang km (xấp xỉ)
                avg_distance_km = avg_distance * 111  # 1 độ ~ 111km
            else:
                avg_distance_km = 0
            
            vessel_groups.append({
                "group_id": i,
                "center": [float(center_lat), float(center_lon)],
                "vessel_count": int(unique_vessels),
                "total_records": len(cluster_data),
                "vessel_types": vessel_types,
                "avg_distance_km": round(avg_distance_km, 2)
            })
        
        # Sắp xếp theo số lượng tàu giảm dần
        vessel_groups.sort(key=lambda x: x["vessel_count"], reverse=True)
        
        # Tạo bản đồ hiển thị các nhóm tàu
        m = folium.Map(location=[df_clean[lat_col].mean(), df_clean[lon_col].mean()], zoom_start=8)
        
        # Màu sắc cho các cụm
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple']
        
        # Thêm các điểm vào bản đồ
        for i in range(n_clusters):
            cluster_data = df_clean[df_clean['cluster'] == i]
            color = colors[i % len(colors)]
            
            # Tạo feature group cho cụm
            fg = folium.FeatureGroup(name=f"Nhóm {i+1} ({len(cluster_data)} điểm)")
            
            # Thêm các điểm vào feature group
            for _, row in cluster_data.iterrows():
                popup_text = f"<b>MMSI:</b> {row[mmsi_col]}<br>"
                
                if vessel_type_col and vessel_type_col in row:
                    popup_text += f"<b>Loại tàu:</b> {row[vessel_type_col]}<br>"
                
                popup_text += f"<b>Vị trí:</b> {row[lat_col]:.4f}, {row[lon_col]:.4f}<br>"
                popup_text += f"<b>Nhóm:</b> {i+1}"
                
                folium.CircleMarker(
                    location=[row[lat_col], row[lon_col]],
                    radius=5,
                    popup=folium.Popup(popup_text, max_width=300),
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7
                ).add_to(fg)
            
            # Thêm đường bao quanh cụm
            if len(cluster_data) > 2:
                from scipy.spatial import ConvexHull
                points = cluster_data[[lon_col, lat_col]].values
                hull = ConvexHull(points)
                hull_points = [points[vertex] for vertex in hull.vertices]
                hull_points.append(hull_points[0])  # Đóng đa giác
                
                # Đổi thứ tự tọa độ (lon, lat) -> (lat, lon) cho folium
                hull_points_folium = [[p[1], p[0]] for p in hull_points]
                
                folium.Polygon(
                    locations=hull_points_folium,
                    color=color,
                    weight=2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.1,
                    popup=f"Nhóm {i+1}: {len(cluster_data)} tàu"
                ).add_to(fg)
            
            fg.add_to(m)
        
        # Thêm điều khiển lớp
        folium.LayerControl().add_to(m)
        
        # Chuyển bản đồ thành HTML
        groups_map_html = m._repr_html_()
        
        return {
            "vessel_groups": vessel_groups,
            "total_groups": n_clusters,
            "total_vessels_in_groups": sum(g["vessel_count"] for g in vessel_groups),
            "map_html": groups_map_html
        }
    except Exception as e:
        return {"error": str(e)}

def extract_hidden_patterns(df):
    """Khai phá các mẫu ẩn trong dữ liệu"""
    try:
        # Tìm cột tọa độ và thời gian
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        time_col = next((col for col in ['BaseDateTime', 'DateTime', 'Timestamp', 'date_time'] if col in df.columns), None)
        
        if not lat_col or not lon_col:
            return {"error": "Không tìm thấy cột tọa độ"}
        
        # Kết quả phân tích
        insights = []
        
        # 1. Phân tích phân bố địa lý
        df_clean = df.dropna(subset=[lat_col, lon_col])
        if len(df_clean) >= 10:
            # Chia thành lưới 4x4
            lat_bins = pd.cut(df_clean[lat_col], 4)
            lon_bins = pd.cut(df_clean[lon_col], 4)
            
            # Đếm số lượng tàu trong mỗi ô lưới
            grid_counts = df_clean.groupby([lat_bins, lon_bins]).size()
            
            # Tìm ô lưới có nhiều tàu nhất
            if not grid_counts.empty:
                max_grid = grid_counts.idxmax()
                max_count = grid_counts.max()
                
                insights.append({
                    "type": "geographic_hotspot",
                    "description": f"Phát hiện khu vực tập trung cao với {max_count} tàu",
                    "details": {
                        "lat_range": str(max_grid[0]),
                        "lon_range": str(max_grid[1]),
                        "count": int(max_count)
                    }
                })
        
        # 2. Phân tích theo thời gian
        if time_col and time_col in df.columns:
            try:
                df['parsed_time'] = pd.to_datetime(df[time_col], errors='coerce')
                df_time = df.dropna(subset=['parsed_time'])
                
                if len(df_time) >= 10:
                    # Phân tích theo giờ trong ngày
                    df_time['hour'] = df_time['parsed_time'].dt.hour
                    hourly_counts = df_time['hour'].value_counts().sort_index()
                    
                    # Tìm giờ cao điểm
                    peak_hour = hourly_counts.idxmax()
                    peak_count = hourly_counts.max()
                    
                    insights.append({
                        "type": "time_pattern",
                        "description": f"Giờ cao điểm là {peak_hour}h với {peak_count} tàu",
                        "details": {
                            "peak_hour": int(peak_hour),
                            "count": int(peak_count)
                        }
                    })
            except:
                pass
        
        # 3. Phân tích mối quan hệ giữa các biến
        speed_col = next((col for col in ['SOG', 'Speed', 'speed'] if col in df.columns), None)
        course_col = next((col for col in ['COG', 'Course', 'course'] if col in df.columns), None)
        
        if speed_col and course_col:
            df_nav = df.dropna(subset=[speed_col, course_col])
            
            if len(df_nav) >= 10:
                # Tính hệ số tương quan
                correlation = df_nav[speed_col].corr(df_nav[course_col])
                
                if not pd.isna(correlation):
                    insights.append({
                        "type": "correlation",
                        "description": f"Hệ số tương quan giữa tốc độ và hướng đi là {correlation:.2f}",
                        "details": {
                            "correlation": float(correlation),
                            "variables": [speed_col, course_col]
                        }
                    })
        
        # 4. Phát hiện các nhóm tàu di chuyển cùng nhau
        vessel_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        if vessel_col and lat_col and lon_col:
            # Sử dụng DBSCAN để phát hiện các nhóm tàu gần nhau
            df_pos = df.dropna(subset=[lat_col, lon_col, vessel_col])
            
            if len(df_pos) >= 20:
                # Chuẩn hóa dữ liệu
                coords = df_pos[[lat_col, lon_col]].values
                coords_scaled = StandardScaler().fit_transform(coords)
                
                # Phát hiện cụm
                db = DBSCAN(eps=0.1, min_samples=3).fit(coords_scaled)
                labels = db.labels_
                
                # Số lượng cụm (không tính nhiễu)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                if n_clusters > 0:
                    # Phân tích thành phần của các cụm
                    df_pos['cluster'] = labels
                    
                    # Tìm cụm có nhiều loại tàu khác nhau nhất
                    diverse_clusters = []
                    
                    for i in range(n_clusters):
                        cluster_data = df_pos[df_pos['cluster'] == i]
                        vessel_types = cluster_data[vessel_col].nunique()
                        
                        if vessel_types > 1:
                            diverse_clusters.append({
                                "cluster_id": i,
                                "vessel_types": int(vessel_types),
                                "total_vessels": len(cluster_data)
                            })
                    
                    if diverse_clusters:
                        # Sắp xếp theo số lượng loại tàu giảm dần
                        diverse_clusters.sort(key=lambda x: x['vessel_types'], reverse=True)
                        top_cluster = diverse_clusters[0]
                        
                        insights.append({
                            "type": "vessel_group",
                            "description": f"Phát hiện nhóm {top_cluster['total_vessels']} tàu thuộc {top_cluster['vessel_types']} loại khác nhau di chuyển gần nhau",
                            "details": top_cluster
                        })
        
        return {
            "insights": insights,
            "total_insights": len(insights)
        }
    except Exception as e:
        return {"error": str(e)}