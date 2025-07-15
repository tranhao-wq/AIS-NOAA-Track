import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_sample_data(n_records=1000, save=True):
    """
    Tạo dữ liệu AIS mẫu để kiểm thử
    
    Parameters:
    -----------
    n_records : int
        Số lượng bản ghi cần tạo
    save : bool
        Lưu dữ liệu vào file CSV hay không
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame chứa dữ liệu mẫu
    """
    # Định nghĩa các loại tàu và tên tàu
    vessel_types = ['Cargo', 'Tanker', 'Passenger', 'Fishing', 'Tug', 'Military', 'Sailing']
    vessel_names = ['Ocean Explorer', 'Pacific Star', 'Atlantic Voyager', 'Northern Light', 
                   'Southern Cross', 'Eastern Wind', 'Western Sun', 'Coastal Runner',
                   'Sea Dragon', 'River Queen', 'Lake Princess', 'Gulf Trader']
    
    # Tạo danh sách MMSI (Maritime Mobile Service Identity) ngẫu nhiên
    mmsi_list = np.random.randint(100000000, 999999999, size=n_records // 10)
    
    # Tạo dữ liệu
    data = []
    base_time = datetime.now()
    
    for i in range(n_records):
        # Chọn một MMSI từ danh sách (để mô phỏng nhiều bản ghi cho cùng một tàu)
        mmsi = np.random.choice(mmsi_list)
        
        # Chọn loại tàu và tên tàu
        vessel_type = np.random.choice(vessel_types)
        vessel_name = np.random.choice(vessel_names) + " " + str(np.random.randint(1, 100))
        
        # Tạo vị trí (tập trung vào một số khu vực để tạo các cụm)
        # Chọn một trong các khu vực tập trung
        area = np.random.randint(0, 5)
        
        if area == 0:  # Khu vực 1
            lat = np.random.uniform(10, 15)
            lon = np.random.uniform(105, 110)
        elif area == 1:  # Khu vực 2
            lat = np.random.uniform(20, 25)
            lon = np.random.uniform(115, 120)
        elif area == 2:  # Khu vực 3
            lat = np.random.uniform(0, 5)
            lon = np.random.uniform(95, 100)
        elif area == 3:  # Khu vực 4
            lat = np.random.uniform(-10, -5)
            lon = np.random.uniform(130, 135)
        else:  # Các tàu rải rác
            lat = np.random.uniform(-30, 30)
            lon = np.random.uniform(90, 140)
        
        # Tạo tốc độ và hướng đi
        # Tốc độ phụ thuộc vào loại tàu
        if vessel_type == 'Cargo':
            sog = np.random.uniform(10, 20)  # Knots
        elif vessel_type == 'Tanker':
            sog = np.random.uniform(8, 15)
        elif vessel_type == 'Passenger':
            sog = np.random.uniform(15, 25)
        elif vessel_type == 'Fishing':
            sog = np.random.uniform(3, 10)
        elif vessel_type == 'Military':
            sog = np.random.uniform(20, 30)
        else:
            sog = np.random.uniform(5, 15)
        
        # Thêm một số giá trị bất thường
        if np.random.random() < 0.05:  # 5% dữ liệu bất thường
            sog = np.random.uniform(30, 50)  # Tốc độ bất thường cao
        
        # Hướng đi (Course Over Ground)
        cog = np.random.uniform(0, 359)
        
        # Thời gian (trong vòng 24 giờ qua)
        time_offset = timedelta(hours=np.random.uniform(0, 24))
        timestamp = (base_time - time_offset).strftime('%Y-%m-%d %H:%M:%S')
        
        # Thêm vào danh sách dữ liệu
        data.append({
            'MMSI': mmsi,
            'VesselName': vessel_name,
            'VesselType': vessel_type,
            'LAT': lat,
            'LON': lon,
            'SOG': sog,
            'COG': cog,
            'BaseDateTime': timestamp,
            'Status': np.random.choice(['Underway', 'At anchor', 'Moored', 'Restricted maneuverability']),
            'Length': np.random.uniform(50, 300) if vessel_type in ['Cargo', 'Tanker', 'Passenger'] else np.random.uniform(10, 50),
            'Width': np.random.uniform(10, 50) if vessel_type in ['Cargo', 'Tanker', 'Passenger'] else np.random.uniform(5, 15),
            'Draft': np.random.uniform(5, 15) if vessel_type in ['Cargo', 'Tanker'] else np.random.uniform(2, 8),
            'Destination': np.random.choice(['SINGAPORE', 'HONG KONG', 'TOKYO', 'MANILA', 'BANGKOK', 'HO CHI MINH', ''])
        })
    
    # Tạo DataFrame
    df = pd.DataFrame(data)
    
    # Luu vao file CSV neu can
    if save:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'AIS_sample_data.csv')
        df.to_csv(output_path, index=False)
        print(f"Da luu du lieu mau vao: {output_path}")
    
    return df

if __name__ == "__main__":
    # Tạo 5000 bản ghi mẫu
    generate_sample_data(5000)