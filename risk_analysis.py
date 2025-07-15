import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import io
import base64

def calculate_risk_scores(df):
    """
    Tính toán điểm rủi ro cho các tàu dựa trên dữ liệu AIS
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame chứa dữ liệu AIS
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame với các cột rủi ro được thêm vào
    """
    try:
        # Tạo bản sao của DataFrame để không ảnh hưởng đến dữ liệu gốc
        risk_df = df.copy()
        
        # Tìm các cột cần thiết
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        speed_col = next((col for col in ['SOG', 'Speed', 'speed'] if col in df.columns), None)
        course_col = next((col for col in ['COG', 'Course', 'course'] if col in df.columns), None)
        vessel_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        if not all([lat_col, lon_col, speed_col]):
            return {"error": "Thiếu các cột dữ liệu cần thiết"}
        
        # 1. Tính toán rủi ro va chạm dựa trên mật độ tàu
        # Tạo lưới không gian và đếm số lượng tàu trong mỗi ô
        lat_bins = np.linspace(df[lat_col].min(), df[lat_col].max(), 20)
        lon_bins = np.linspace(df[lon_col].min(), df[lon_col].max(), 20)
        
        # Gán nhóm cho mỗi tàu
        risk_df['lat_bin'] = pd.cut(risk_df[lat_col], bins=lat_bins, labels=False)
        risk_df['lon_bin'] = pd.cut(risk_df[lon_col], bins=lon_bins, labels=False)
        
        # Đếm số lượng tàu trong mỗi ô lưới
        grid_counts = risk_df.groupby(['lat_bin', 'lon_bin']).size().reset_index(name='vessel_count')
        
        # Gộp lại với DataFrame gốc
        risk_df = pd.merge(risk_df, grid_counts, on=['lat_bin', 'lon_bin'], how='left')
        
        # Chuẩn hóa số lượng tàu thành điểm rủi ro va chạm (0-100)
        max_count = risk_df['vessel_count'].max()
        risk_df['CollisionRisk'] = (risk_df['vessel_count'] / max_count * 100).clip(0, 100)
        
        # 2. Tính toán rủi ro thời tiết (giả lập)
        # Trong thực tế, sẽ sử dụng dữ liệu thời tiết thực tế
        # Ở đây, chúng ta giả lập dựa trên vị trí và thời gian
        np.random.seed(42)  # Để kết quả nhất quán
        risk_df['WeatherRisk'] = np.random.uniform(20, 80, size=len(risk_df))
        
        # Điều chỉnh rủi ro thời tiết dựa trên vĩ độ (giả định thời tiết xấu hơn ở vĩ độ cao)
        risk_df['WeatherRisk'] = risk_df['WeatherRisk'] + (abs(risk_df[lat_col]) / 90 * 20)
        risk_df['WeatherRisk'] = risk_df['WeatherRisk'].clip(0, 100)
        
        # 3. Tính toán rủi ro lệch tuyến đường
        if vessel_col in risk_df.columns:
            # Tính trung bình vị trí cho mỗi loại tàu
            vessel_avg_positions = risk_df.groupby(vessel_col)[[lat_col, lon_col]].mean().reset_index()
            vessel_avg_positions.columns = [vessel_col, 'avg_lat', 'avg_lon']
            
            # Gộp lại với DataFrame gốc
            risk_df = pd.merge(risk_df, vessel_avg_positions, on=vessel_col, how='left')
            
            # Tính khoảng cách từ vị trí hiện tại đến vị trí trung bình
            risk_df['dist_from_avg'] = np.sqrt((risk_df[lat_col] - risk_df['avg_lat'])**2 + 
                                              (risk_df[lon_col] - risk_df['avg_lon'])**2)
            
            # Chuẩn hóa thành điểm rủi ro lệch tuyến đường
            max_dist = risk_df['dist_from_avg'].max()
            if max_dist > 0:
                risk_df['RouteDeviation'] = (risk_df['dist_from_avg'] / max_dist * 100).clip(0, 100)
            else:
                risk_df['RouteDeviation'] = 0
        else:
            # Nếu không có thông tin loại tàu, gán giá trị mặc định
            risk_df['RouteDeviation'] = 50
        
        # 4. Tính toán rủi ro tốc độ bất thường
        if speed_col in risk_df.columns:
            # Tính ngưỡng tốc độ bất thường (phương pháp IQR)
            Q1 = risk_df[speed_col].quantile(0.25)
            Q3 = risk_df[speed_col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Tính độ lệch so với ngưỡng
            risk_df['speed_deviation'] = 0
            risk_df.loc[risk_df[speed_col] < lower_bound, 'speed_deviation'] = (lower_bound - risk_df[speed_col]) / lower_bound * 100
            risk_df.loc[risk_df[speed_col] > upper_bound, 'speed_deviation'] = (risk_df[speed_col] - upper_bound) / upper_bound * 100
            
            # Chuẩn hóa thành điểm rủi ro tốc độ bất thường
            risk_df['SpeedAnomaly'] = risk_df['speed_deviation'].clip(0, 100)
        else:
            # Nếu không có thông tin tốc độ, gán giá trị mặc định
            risk_df['SpeedAnomaly'] = 50
        
        # 5. Tính toán rủi ro chướng ngại vật hàng hải (giả lập)
        # Trong thực tế, sẽ sử dụng dữ liệu về chướng ngại vật thực tế
        # Ở đây, chúng ta giả lập dựa trên vị trí
        np.random.seed(123)  # Để kết quả nhất quán
        risk_df['NavigationHazard'] = np.random.uniform(10, 60, size=len(risk_df))
        
        # Tạo một số "điểm nóng" nguy hiểm
        hazard_points = [
            {'lat': df[lat_col].min() + (df[lat_col].max() - df[lat_col].min()) * 0.3, 
             'lon': df[lon_col].min() + (df[lon_col].max() - df[lon_col].min()) * 0.7},
            {'lat': df[lat_col].min() + (df[lat_col].max() - df[lat_col].min()) * 0.7, 
             'lon': df[lon_col].min() + (df[lon_col].max() - df[lon_col].min()) * 0.2},
            {'lat': df[lat_col].min() + (df[lat_col].max() - df[lat_col].min()) * 0.5, 
             'lon': df[lon_col].min() + (df[lon_col].max() - df[lon_col].min()) * 0.5}
        ]
        
        # Tính khoảng cách đến các điểm nguy hiểm và tăng rủi ro nếu gần
        for point in hazard_points:
            dist = np.sqrt((risk_df[lat_col] - point['lat'])**2 + (risk_df[lon_col] - point['lon'])**2)
            max_effect_dist = 0.1  # Ngưỡng khoảng cách có ảnh hưởng
            risk_increase = np.maximum(0, (1 - dist / max_effect_dist) * 40)  # Tăng tối đa 40 điểm
            risk_df['NavigationHazard'] = np.minimum(100, risk_df['NavigationHazard'] + risk_increase)
        
        # 6. Tính điểm rủi ro tổng hợp
        # Trọng số cho từng loại rủi ro
        weights = {
            'CollisionRisk': 0.3,
            'WeatherRisk': 0.2,
            'RouteDeviation': 0.15,
            'SpeedAnomaly': 0.2,
            'NavigationHazard': 0.15
        }
        
        # Tính điểm rủi ro tổng hợp
        risk_df['RiskScore'] = (
            weights['CollisionRisk'] * risk_df['CollisionRisk'] +
            weights['WeatherRisk'] * risk_df['WeatherRisk'] +
            weights['RouteDeviation'] * risk_df['RouteDeviation'] +
            weights['SpeedAnomaly'] * risk_df['SpeedAnomaly'] +
            weights['NavigationHazard'] * risk_df['NavigationHazard']
        )
        
        # Làm tròn các giá trị
        for col in ['CollisionRisk', 'WeatherRisk', 'RouteDeviation', 'SpeedAnomaly', 'NavigationHazard', 'RiskScore']:
            risk_df[col] = risk_df[col].round(1)
        
        # Loại bỏ các cột tạm thời
        risk_df = risk_df.drop(['lat_bin', 'lon_bin', 'vessel_count', 'dist_from_avg', 'speed_deviation'], axis=1, errors='ignore')
        if 'avg_lat' in risk_df.columns:
            risk_df = risk_df.drop(['avg_lat', 'avg_lon'], axis=1)
        
        return risk_df
    
    except Exception as e:
        return {"error": str(e)}

def identify_risky_routes(df, risk_threshold=70):
    """
    Xác định các hành trình có rủi ro cao
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame chứa dữ liệu AIS với điểm rủi ro
    risk_threshold : float
        Ngưỡng điểm rủi ro để xác định hành trình nguy hiểm
    
    Returns:
    --------
    list
        Danh sách các hành trình có rủi ro cao
    """
    try:
        # Kiểm tra xem DataFrame đã có điểm rủi ro chưa
        if 'RiskScore' not in df.columns:
            df = calculate_risk_scores(df)
            if isinstance(df, dict) and "error" in df:
                return df
        
        # Lọc các tàu có điểm rủi ro cao
        risky_vessels = df[df['RiskScore'] >= risk_threshold]
        
        # Tìm các cột cần thiết
        mmsi_col = next((col for col in ['MMSI', 'mmsi', 'VesselId'] if col in df.columns), None)
        vessel_name_col = next((col for col in ['VesselName', 'vessel_name', 'Name'] if col in df.columns), None)
        vessel_type_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        
        # Tạo danh sách các hành trình có rủi ro cao
        risky_routes = []
        
        # Nhóm theo tàu (MMSI)
        if mmsi_col:
            for mmsi, group in risky_vessels.groupby(mmsi_col):
                vessel_name = group[vessel_name_col].iloc[0] if vessel_name_col in group.columns else "Unknown"
                vessel_type = group[vessel_type_col].iloc[0] if vessel_type_col in group.columns else "Unknown"
                
                # Lấy điểm rủi ro cao nhất
                max_risk_idx = group['RiskScore'].idxmax()
                max_risk_row = group.loc[max_risk_idx]
                
                # Tạo mô tả rủi ro
                risk_descriptions = []
                if max_risk_row['CollisionRisk'] >= 70:
                    risk_descriptions.append("nguy cơ va chạm cao")
                if max_risk_row['WeatherRisk'] >= 70:
                    risk_descriptions.append("điều kiện thời tiết xấu")
                if max_risk_row['RouteDeviation'] >= 70:
                    risk_descriptions.append("lệch tuyến đường đáng kể")
                if max_risk_row['SpeedAnomaly'] >= 70:
                    risk_descriptions.append("tốc độ bất thường")
                if max_risk_row['NavigationHazard'] >= 70:
                    risk_descriptions.append("gần chướng ngại vật nguy hiểm")
                
                if not risk_descriptions:
                    risk_descriptions.append("nhiều yếu tố rủi ro kết hợp")
                
                description = "Tàu đang có " + ", ".join(risk_descriptions)
                
                # Tạo đối tượng hành trình rủi ro
                route = {
                    'mmsi': mmsi,
                    'vesselName': vessel_name,
                    'vesselType': vessel_type,
                    'riskScore': float(max_risk_row['RiskScore']),
                    'riskFactors': {
                        'collision': float(max_risk_row['CollisionRisk']),
                        'weather': float(max_risk_row['WeatherRisk']),
                        'route': float(max_risk_row['RouteDeviation']),
                        'speed': float(max_risk_row['SpeedAnomaly']),
                        'navigation': float(max_risk_row['NavigationHazard'])
                    },
                    'location': [float(max_risk_row[lat_col]), float(max_risk_row[lon_col])] if lat_col and lon_col else [0, 0],
                    'description': description
                }
                
                risky_routes.append(route)
        
        # Sắp xếp theo điểm rủi ro giảm dần
        risky_routes.sort(key=lambda x: x['riskScore'], reverse=True)
        
        return risky_routes
    
    except Exception as e:
        return {"error": str(e)}

def generate_risk_map(df):
    """
    Tạo bản đồ hiển thị các khu vực có rủi ro cao sử dụng Leaflet
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame chứa dữ liệu AIS với điểm rủi ro
    
    Returns:
    --------
    str
        HTML của bản đồ rủi ro
    """
    try:
        # Kiểm tra xem DataFrame đã có điểm rủi ro chưa
        if 'RiskScore' not in df.columns:
            df = calculate_risk_scores(df)
            if isinstance(df, dict) and "error" in df:
                return f"<div>Lỗi: {df['error']}</div>"
        
        # Tìm các cột cần thiết
        lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
        lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
        
        if not lat_col or not lon_col:
            return "<div>Không tìm thấy cột tọa độ</div>"
        
        # Lọc dữ liệu hợp lệ
        df_clean = df.dropna(subset=[lat_col, lon_col, 'RiskScore'])
        df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
        df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
        
        if len(df_clean) < 1:
            return "<div>Không đủ dữ liệu để tạo bản đồ rủi ro</div>"
        
        # Tính toán trung tâm bản đồ
        center_lat = df_clean[lat_col].mean()
        center_lon = df_clean[lon_col].mean()
        
        # Tạo bản đồ sử dụng Leaflet
        map_html = f'''
        <div id="risk-map-container" style="height: 600px; width: 100%; border-radius: 10px;"></div>
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
                
                // Đợi Leaflet và các plugin tải xong
                var checkInterval = setInterval(function() {{
                    if (typeof L !== 'undefined' && typeof L.heatLayer !== 'undefined') {{
                        clearInterval(checkInterval);
                        initRiskMap();
                    }}
                }}, 100);
            }} else {{
                // Leaflet đã được tải, khởi tạo bản đồ ngay lập tức
                initRiskMap();
            }}
            
            function initRiskMap() {{
                // Tạo bản đồ
                var map = L.map('risk-map-container').setView([{center_lat}, {center_lon}], 8);
                
                // Thêm lớp bản đồ nền
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Dữ liệu cho bản đồ nhiệt rủi ro
                var heatData = [
        '''
        
        # Tạo dữ liệu cho bản đồ nhiệt rủi ro
        heat_data = []
        for _, row in df_clean.iterrows():
            # Trọng số dựa trên điểm rủi ro
            weight = float(row['RiskScore']) / 100 * 2  # Nhân với 2 để tăng cường hiệu ứng
            heat_data.append(f"[{float(row[lat_col])}, {float(row[lon_col])}, {weight}]")
        
        # Thêm dữ liệu vào mã JavaScript
        map_html += ',\n                    '.join(heat_data)
        
        # Thêm các điểm rủi ro cao
        high_risk_vessels = df_clean[df_clean['RiskScore'] >= 70]
        
        mmsi_col = next((col for col in ['MMSI', 'mmsi', 'VesselId'] if col in df.columns), None)
        vessel_name_col = next((col for col in ['VesselName', 'vessel_name', 'Name'] if col in df.columns), None)
        vessel_type_col = next((col for col in ['VesselType', 'ShipType', 'vessel_type'] if col in df.columns), None)
        
        map_html += '''
                ];
                
                // Tạo bản đồ nhiệt
                var heatLayer = L.heatLayer(heatData, {{
                    radius: 20,
                    blur: 15,
                    maxZoom: 10,
                    max: 1.0,
                    gradient: {{0.4: 'blue', 0.65: 'yellow', 0.9: 'red'}}
                }}).addTo(map);
                
                // Thêm các điểm rủi ro cao
                var highRiskPoints = [
        '''
        
        # Thêm các điểm rủi ro cao
        high_risk_points = []
        for _, row in high_risk_vessels.iterrows():
            # Tạo popup text
            popup_text = f"Điểm rủi ro: {row['RiskScore']}"
            
            if mmsi_col and mmsi_col in row:
                popup_text += f"<br>MMSI: {row[mmsi_col]}"
            
            if vessel_name_col and vessel_name_col in row:
                popup_text += f"<br>Tàu: {row[vessel_name_col]}"
            
            if vessel_type_col and vessel_type_col in row:
                popup_text += f"<br>Loại: {row[vessel_type_col]}"
            
            popup_text += f"<br>Vị trí: {row[lat_col]:.4f}, {row[lon_col]:.4f}"
            popup_text += "<br>Các yếu tố rủi ro:"
            popup_text += f"<br>- Va chạm: {row['CollisionRisk']}"
            popup_text += f"<br>- Thời tiết: {row['WeatherRisk']}"
            popup_text += f"<br>- Lệch tuyến: {row['RouteDeviation']}"
            popup_text += f"<br>- Tốc độ bất thường: {row['SpeedAnomaly']}"
            popup_text += f"<br>- Chướng ngại vật: {row['NavigationHazard']}"
            
            # Escape single quotes
            popup_text = popup_text.replace("'", "\\'") 
            
            high_risk_points.append(f"[{float(row[lat_col])}, {float(row[lon_col])}, '{popup_text}']")
        
        # Thêm các điểm vào mã JavaScript
        map_html += ',\n                    '.join(high_risk_points)
        
        # Hoàn thành mã JavaScript
        map_html += '''
                ];
                
                // Thêm các điểm rủi ro cao vào bản đồ
                highRiskPoints.forEach(function(point) {
                    var lat = point[0];
                    var lon = point[1];
                    var popupText = point[2];
                    
                    L.circleMarker([lat, lon], {
                        radius: 8,
                        color: 'red',
                        fillColor: 'red',
                        fillOpacity: 0.7,
                        weight: 2
                    }).bindPopup(popupText).addTo(map);
                });
                
                // Thêm chú thích
                var legend = L.control({position: 'bottomright'});
                legend.onAdd = function(map) {
                    var div = L.DomUtil.create('div', 'info legend');
                    div.style.backgroundColor = 'white';
                    div.style.padding = '10px';
                    div.style.borderRadius = '5px';
                    div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                    
                    div.innerHTML = '<h4 style="margin-top: 0;">⚠️ Mức độ rủi ro</h4>';
                    
                    // Thêm các mức độ rủi ro vào chú thích
                    div.innerHTML += 
                        '<div style="display: flex; align-items: center; margin-bottom: 5px;">' +
                        '<div style="width: 20px; height: 20px; background: red; margin-right: 5px;"></div>' +
                        '<span>Rủi ro cao (>70)</span></div>';
                        
                    div.innerHTML += 
                        '<div style="display: flex; align-items: center; margin-bottom: 5px;">' +
                        '<div style="width: 20px; height: 20px; background: yellow; margin-right: 5px;"></div>' +
                        '<span>Rủi ro trung bình (40-70)</span></div>';
                        
                    div.innerHTML += 
                        '<div style="display: flex; align-items: center;">' +
                        '<div style="width: 20px; height: 20px; background: blue; margin-right: 5px;"></div>' +
                        '<span>Rủi ro thấp (<40)</span></div>';
                    
                    return div;
                };
                legend.addTo(map);
            }
        </script>
        '''
        
        return map_html
    
    except Exception as e:
        return f"<div>Lỗi khi tạo bản đồ rủi ro: {str(e)}</div>"