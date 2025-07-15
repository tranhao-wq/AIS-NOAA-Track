from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import requests
import pandas as pd
import zipfile
from io import BytesIO, StringIO
import folium
from datetime import datetime
import asyncio
import aiohttp
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import glob

# Import module phân tích dữ liệu
import analytics
import risk_analysis
import api_endpoints
import requests
from urllib.parse import urlencode

app = FastAPI(title="AIS Data Analyzer", description="Marine Traffic Analysis Tool")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class VesselFilter(BaseModel):
    vessel_types: Optional[List[str]] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DownloadRequest(BaseModel):
    url: str

# Global storage for processed data
processed_data = {}

# Load data from local files on startup
@app.on_event("startup")
async def load_local_data():
    """
    Load AIS data from local data directory on startup
    """
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.exists(data_dir):
            print(f"[INFO] Data directory not found: {data_dir}")
            return
            
        # Look for CSV files in the data directory
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
        if not csv_files:
            print(f"[INFO] No CSV files found in data directory: {data_dir}")
            return
            
        # Use the first CSV file found
        csv_file = csv_files[0]
        print(f"[INFO] Loading data from: {csv_file}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file, low_memory=False)
        
        if df is None or df.empty:
            print("[WARNING] No data found in the file")
            return
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        # Store processed data
        processed_data['original'] = df
        processed_data['filtered'] = df.copy()
        
        # Generate statistics
        stats = generate_statistics(df)
        print(f"[INFO] Successfully loaded {len(df)} records from local data")
        
    except Exception as e:
        print(f"[ERROR] Failed to load local data: {str(e)}")

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process AIS data file (CSV or ZIP)
    """
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        # Process data based on file type
        df = None
        if filename.endswith('.zip'):
            with zipfile.ZipFile(BytesIO(content)) as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                if not csv_files:
                    raise HTTPException(status_code=400, detail="No CSV files found in ZIP archive")
                
                # Read the first CSV file
                with zip_file.open(csv_files[0]) as csv_file:
                    df = pd.read_csv(csv_file, low_memory=False)
        elif filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content), low_memory=False)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please provide CSV or ZIP file.")
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="No data found in the file")
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        # Store processed data
        processed_data['original'] = df
        processed_data['filtered'] = df.copy()
        
        # Generate statistics
        stats = generate_statistics(df)
        
        return {
            "total_records": len(df),
            "stats": stats,
            "message": "File uploaded and processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {str(e)}")

@app.get("/generate-sample-data")
async def generate_sample_data():
    """
    Generate sample AIS data for testing without downloading
    """
    try:
        # Create sample data with common AIS fields
        import random
        from datetime import datetime, timedelta
        
        # Define vessel types and names
        vessel_types = ['Cargo', 'Tanker', 'Passenger', 'Fishing', 'Tug', 'Military', 'Sailing']
        vessel_names = ['Ocean Explorer', 'Pacific Star', 'Atlantic Voyager', 'Northern Light', 
                       'Southern Cross', 'Eastern Wind', 'Western Sun', 'Coastal Runner',
                       'Sea Dragon', 'River Queen', 'Lake Princess', 'Gulf Trader']
        
        # Generate random data
        data = []
        base_time = datetime.now()
        
        # Generate 1000 random vessel positions
        for i in range(1000):
            mmsi = random.randint(100000000, 999999999)
            vessel_type = random.choice(vessel_types)
            vessel_name = random.choice(vessel_names) + " " + str(random.randint(1, 100))
            
            # Generate positions around the world
            lat = random.uniform(-80, 80)
            lon = random.uniform(-179, 179)
            
            # Random speed and course
            sog = random.uniform(0, 20)  # Speed Over Ground in knots
            cog = random.uniform(0, 359)  # Course Over Ground in degrees
            
            # Random timestamp within the last 24 hours
            time_offset = timedelta(hours=random.uniform(0, 24))
            timestamp = (base_time - time_offset).strftime('%Y-%m-%d %H:%M:%S')
            
            data.append({
                'MMSI': mmsi,
                'VesselName': vessel_name,
                'VesselType': vessel_type,
                'LAT': lat,
                'LON': lon,
                'SOG': sog,
                'COG': cog,
                'BaseDateTime': timestamp
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Store processed data
        processed_data['original'] = df
        processed_data['filtered'] = df.copy()
        
        # Generate statistics
        stats = generate_statistics(df)
        
        return {
            "total_records": len(df),
            "stats": stats,
            "message": "Sample data generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample data: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIS Data Analyzer</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 { 
                color: #2c3e50; 
                text-align: center; 
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .form-group { 
                margin: 20px 0; 
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #007bff;
            }
            .form-group h3 {
                margin-top: 0;
                color: #495057;
            }
            input, select, button { 
                padding: 12px; 
                margin: 8px; 
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            input[type="url"] {
                width: 400px;
            }
            input[type="number"] {
                width: 120px;
            }
            select {
                min-width: 150px;
            }
            button { 
                background: linear-gradient(45deg, #007bff, #0056b3); 
                color: white; 
                border: none; 
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,123,255,0.3);
            }
            .results { 
                margin-top: 30px; 
            }
            #map { 
                height: 600px; 
                width: 100%; 
                margin: 20px 0; 
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            #status {
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                font-weight: bold;
            }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            #stats {
                background: #e9ecef;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            
            /* Tab Navigation */
            .tab-navigation {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-bottom: 20px;
            }
            
            .tab-button {
                padding: 10px 15px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 500;
                color: #495057;
                transition: all 0.2s;
            }
            
            .tab-button:hover {
                background: #e9ecef;
            }
            
            .tab-button.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            
            /* Tab Content */
            .tab-content {
                display: none;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .tab-content.active {
                display: block;
            }
            
            /* Analytics Sections */
            .analytics-section {
                margin-bottom: 30px;
                padding: 20px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .result-container {
                margin-top: 15px;
                padding: 15px;
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                min-height: 100px;
            }
            
            .chart-container {
                margin: 20px 0;
                text-align: center;
            }
            
            /* Insights styling */
            .insights-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            
            .insight-card {
                background: white;
                border-left: 4px solid #007bff;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .insight-card h5 {
                margin-top: 0;
                color: #343a40;
            }
            
            /* Loading animation */
            .loading {
                display: inline-block;
                width: 30px;
                height: 30px;
                border: 3px solid rgba(0,123,255,0.3);
                border-radius: 50%;
                border-top-color: #007bff;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Risky Routes Styling */
            .risky-routes-container {
                display: flex;
                flex-direction: column;
                gap: 15px;
                margin-top: 20px;
            }
            
            .risky-route-card {
                display: flex;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .risk-score {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 80px;
                font-size: 24px;
                font-weight: bold;
                color: white;
            }
            
            .route-details {
                flex: 1;
                padding: 15px;
            }
            
            .route-details h5 {
                margin-top: 0;
                margin-bottom: 10px;
            }
            
            .risk-factors {
                margin-top: 10px;
            }
            
            .risk-factor {
                height: 20px;
                margin-bottom: 5px;
                background: linear-gradient(90deg, #007bff, #0056b3);
                color: white;
                font-size: 12px;
                line-height: 20px;
                padding: 0 8px;
                border-radius: 3px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            /* Risk Stats Styling */
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
            
            /* Risk Dashboard Layout */
            .risk-dashboard {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 20px;
            }
            
            .risk-panel {
                flex: 1;
                min-width: 300px;
            }
            
            .risk-results-panel {
                flex: 2;
                min-width: 400px;
            }
            
            /* Risk Factors Explanation */
            .risk-factors-explanation {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            
            .risk-factor-card {
                display: flex;
                margin-bottom: 15px;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            
            .risk-factor-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 50px;
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
            
            .risk-factor-info {
                flex: 1;
                padding: 10px 15px;
            }
            
            .risk-factor-info h5 {
                margin: 0 0 5px 0;
            }
            
            .risk-factor-info p {
                margin: 0;
                font-size: 14px;
                color: #6c757d;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .stat-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #007bff;
            }
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script src="/static/js/map_helper.js"></script>
        <script src="/static/js/risk_analysis.js"></script>
        <script src="/static/js/marine_cadastre.js"></script>
        <script src="/static/js/welcome.js"></script>
        <script src="/static/js/tab_animation.js"></script>
        <script src="/static/js/dashboard.js"></script>
        <script src="/static/js/risk_map.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>🚢 AIS Marine Traffic Analyzer</h1>
            
            <div class="form-group">
                <h3>📥 AIS Data Sources</h3>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                    <div style="flex: 1; min-width: 300px;">
                        <h4>Upload Local File</h4>
                        <form id="uploadForm" enctype="multipart/form-data">
                            <input type="file" id="fileInput" accept=".csv,.zip" style="margin-bottom: 10px;">
                            <button type="button" onclick="uploadFile()" style="background: linear-gradient(45deg, #17a2b8, #138496);">
                                <span id="uploadBtn">Upload & Process</span>
                            </button>
                        </form>
                    </div>
                    
                    <div style="flex: 1; min-width: 300px;">
                        <h4>Download from URL</h4>
                        <input type="url" id="aisUrl" placeholder="https://coast.noaa.gov/htdata/CMSP/AISDataHandler/..." style="width: 100%; margin-bottom: 10px;">
                        <button onclick="downloadData()">
                            <span id="downloadBtn">Download & Process</span>
                        </button>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="generateSampleData()" style="background: linear-gradient(45deg, #28a745, #218838);">
                        Generate Sample Data
                    </button>
                    <button onclick="checkLocalData()" style="background: linear-gradient(45deg, #fd7e14, #e96b02);">
                        Use Local Data
                    </button>
                </div>
            </div>
            
            <div class="form-group">
                <h3>🔍 Filter Data</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <div>
                        <label>Vessel Types:</label><br>
                        <select id="vesselType" multiple style="height: 100px; width: 100%;">
                            <option value="Cargo">Cargo Ships</option>
                            <option value="Tanker">Tankers</option>
                            <option value="Passenger">Passenger Ships</option>
                            <option value="Fishing">Fishing Vessels</option>
                            <option value="Tug">Tug Boats</option>
                            <option value="Military">Military</option>
                            <option value="Sailing">Sailing</option>
                        </select>
                    </div>
                    <div>
                        <label>Latitude Range:</label><br>
                        <input type="number" id="minLat" placeholder="Min Lat" step="0.001">
                        <input type="number" id="maxLat" placeholder="Max Lat" step="0.001">
                    </div>
                    <div>
                        <label>Longitude Range:</label><br>
                        <input type="number" id="minLon" placeholder="Min Lon" step="0.001">
                        <input type="number" id="maxLon" placeholder="Max Lon" step="0.001">
                    </div>
                </div>
                <button onclick="filterData()" style="margin-top: 15px;">Apply Filters</button>
                <button onclick="clearFilters()" style="background: #6c757d;">Clear Filters</button>
                <button onclick="exportData()" style="background: #28a745;">Export CSV</button>
            </div>
            
            <!-- Tab Navigation -->
            <div class="tab-navigation" style="margin-top: 20px;">
                <button id="tab-basic" class="tab-button active" onclick="switchTab('basic')">Bản đồ cơ bản</button>
                <button id="tab-advanced" class="tab-button" onclick="switchTab('advanced')">Bản đồ nâng cao</button>
                <button id="tab-marine" class="tab-button" onclick="switchTab('marine')">Marine Cadastre</button>
                <button id="tab-analytics" class="tab-button" onclick="switchTab('analytics')">Phân tích dữ liệu</button>
                <button id="tab-dashboard" class="tab-button" onclick="switchTab('dashboard')">Dashboard</button>
                <button id="tab-predictions" class="tab-button" onclick="switchTab('predictions')">Dự đoán</button>
                <button id="tab-hidden" class="tab-button" onclick="switchTab('hidden')">Dữ liệu ẩn</button>
                <button id="tab-risk" class="tab-button" onclick="switchTab('risk')">Hành trình rủi ro</button>
            </div>
            
            <div class="results">
                <div id="status"></div>
                <div id="stats"></div>
                
                <!-- Tab Content -->
                <div id="tab-content-basic" class="tab-content active">
                    <div id="map"></div>
                    <div id="map-trust-message" style="display: none; margin-top: 10px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px;">
                        <p><strong>Lưu ý:</strong> Nếu bạn thấy thông báo "Make this Notebook Trusted to load map", hãy nhấp vào nút bên dưới để hiển thị bản đồ:</p>
                        <button onclick="trustMap()" style="background: #ffc107; color: #212529; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer;">Hiển thị bản đồ</button>
                    </div>
                </div>
                
                <div id="tab-content-advanced" class="tab-content">
                    <h3>🗺️ Bản đồ nâng cao</h3>
                    <p>Bản đồ nâng cao hiển thị nhiều lớp dữ liệu khác nhau, bao gồm cụm tàu, bản đồ nhiệt và các lớp theo loại tàu.</p>
                    <button onclick="loadAdvancedMap()" style="background: linear-gradient(45deg, #6f42c1, #6610f2); margin-bottom: 15px;">
                        Tải bản đồ nâng cao
                    </button>
                    <div id="advanced-map" style="height: 600px; width: 100%; border-radius: 10px; overflow: hidden;"></div>
                </div>
                
                <div id="tab-content-analytics" class="tab-content">
                    <h3>📈 Phân tích dữ liệu</h3>
                    
                    <div class="analytics-section">
                        <h4>🔍 Phát hiện mẫu di chuyển</h4>
                        <p>Phát hiện các mẫu di chuyển bất thường của tàu thuyền.</p>
                        <button onclick="detectPatterns()" style="background: linear-gradient(45deg, #20c997, #0ca678);">
                            Phát hiện mẫu
                        </button>
                        <div id="patterns-result" class="result-container"></div>
                    </div>
                    
                    <div class="analytics-section">
                        <h4>📁 Phân tích loại tàu</h4>
                        <p>Phân tích chi tiết theo loại tàu và tốc độ di chuyển.</p>
                        <button onclick="analyzeVesselTypes()" style="background: linear-gradient(45deg, #fd7e14, #e96b02);">
                            Phân tích loại tàu
                        </button>
                        <div id="vessel-types-result" class="result-container"></div>
                    </div>
                    
                    <div class="analytics-section">
                        <h4>⚠️ Phát hiện dữ liệu bất thường</h4>
                        <p>Phát hiện các dữ liệu bất thường về tốc độ, vị trí hoặc hành vi.</p>
                        <button onclick="detectAnomalies()" style="background: linear-gradient(45deg, #dc3545, #c82333);">
                            Phát hiện bất thường
                        </button>
                        <div id="anomalies-result" class="result-container"></div>
                    </div>
                </div>
                
                <div id="tab-content-predictions" class="tab-content">
                    <h3>🔮 Dự đoán</h3>
                    <p>Dự đoán mật độ tàu thuyền trong các khu vực dựa trên dữ liệu hiện tại.</p>
                    
                    <button onclick="predictDensity()" style="background: linear-gradient(45deg, #17a2b8, #138496); margin-bottom: 15px;">
                        Dự đoán mật độ
                    </button>
                    
                    <div id="density-result" class="result-container"></div>
                </div>
                
                <div id="tab-content-hidden" class="tab-content">
                    <h3>🔎 Khai phá dữ liệu ẩn</h3>
                    <p>Khai phá các mẫu ẩn và thông tin chưa được khám phá trong dữ liệu.</p>
                    
                    <button onclick="extractHiddenPatterns()" style="background: linear-gradient(45deg, #6f42c1, #6610f2); margin-bottom: 15px;">
                        Khai phá dữ liệu ẩn
                    </button>
                    
                    <div id="hidden-result" class="result-container"></div>
                </div>
                
                <div id="tab-content-dashboard" class="tab-content">
                    <h3>📊 Bảng điều khiển phân tích</h3>
                    <p>Tổng hợp các phân tích nâng cao từ dữ liệu AIS, bao gồm phân tích tương quan, phân tích thời gian và phát hiện nhóm tàu.</p>
                    
                    <button onclick="loadDashboard()" style="background: linear-gradient(45deg, #007bff, #0056b3); margin-bottom: 15px;">
                        Tải dữ liệu phân tích
                    </button>
                    
                    <div id="dashboard-container" class="result-container">
                        <div class="dashboard-placeholder">
                            <div class="placeholder-icon">📊</div>
                            <h4>Bảng điều khiển phân tích</h4>
                            <p>Nhấn nút "Tải dữ liệu phân tích" để xem các phân tích nâng cao từ dữ liệu AIS.</p>
                        </div>
                    </div>
                </div>
                
                <div id="tab-content-marine" class="tab-content">
                    <h3>🌍 Marine Cadastre AIS Map</h3>
                    <p>Bản đồ tích hợp trực tiếp từ marinecadastre.gov với dữ liệu AIS.</p>
                    
                    <div class="marine-controls" style="margin-bottom: 15px;">
                        <button onclick="loadMarineCadastreMap()" style="background: linear-gradient(45deg, #0077b6, #0096c7);">
                            Tải bản đồ Marine Cadastre
                        </button>
                        <a href="https://marinecadastre.gov/nationalviewer/" target="_blank" style="display: inline-block; margin-left: 10px; padding: 12px 20px; background: linear-gradient(45deg, #20c997, #0ca678); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Mở trong cửa sổ mới
                        </a>
                    </div>
                    
                    <div id="marine-map" style="height: 700px; width: 100%; border-radius: 10px; overflow: hidden; border: 2px solid #0077b6;">
                        <iframe src="https://marinecadastre.gov/nationalviewer/" style="width: 100%; height: 100%; border: none;"></iframe>
                    </div>
                    
                    <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #0077b6;">
                        <h4>Về Marine Cadastre</h4>
                        <p>Marine Cadastre là một nền tảng cung cấp dữ liệu không gian biển và công cụ hỗ trợ quyết định cho các nhà quản lý, nhà hoạch định và các bên liên quan đến đại dương.</p>
                        <p>Dữ liệu AIS từ Marine Cadastre cung cấp thông tin về chuyển động của tàu thuyền, giúp cải thiện an toàn hàng hải và bảo vệ môi trường biển.</p>
                    </div>
                </div>
                
                <div id="tab-content-risk" class="tab-content">
                    <h3>⚠️ Phân tích hành trình rủi ro</h3>
                    <p>Dự đoán và phân tích các hành trình có rủi ro cao dựa trên dữ liệu AIS.</p>
                    
                    <div class="risk-dashboard">
                        <div class="risk-panel">
                            <div class="risk-controls" style="margin-bottom: 20px;">
                                <h4>Thiết lập phân tích rủi ro</h4>
                                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">
                                    <div>
                                        <label>Ngưỡng điểm rủi ro:</label>
                                        <input type="range" id="risk-threshold" min="0" max="100" value="70" style="width: 200px;">
                                        <span id="risk-threshold-value">70</span>
                                    </div>
                                    <div>
                                        <label>Loại rủi ro:</label>
                                        <select id="risk-type" multiple style="height: 80px; width: 200px;">
                                            <option value="collision" selected>Va chạm</option>
                                            <option value="weather" selected>Thời tiết</option>
                                            <option value="route" selected>Lệch tuyến đường</option>
                                            <option value="speed" selected>Tốc độ bất thường</option>
                                            <option value="navigation" selected>Chướng ngại vật</option>
                                        </select>
                                    </div>
                                </div>
                                <button onclick="analyzeRiskyRoutes()" style="background: linear-gradient(45deg, #d00000, #dc2f02); margin-right: 10px;">
                                    Phân tích hành trình rủi ro
                                </button>
                                <button onclick="showRiskMap()" style="background: linear-gradient(45deg, #6a4c93, #8338ec);">
                                    Hiển thị bản đồ rủi ro
                                </button>
                            </div>
                            
                            <!-- Risk Factors Explanation -->
                            <div class="risk-factors-explanation">
                                <h4>Các yếu tố rủi ro</h4>
                                <div class="risk-factor-card">
                                    <div class="risk-factor-icon" style="background: #dc3545;">C</div>
                                    <div class="risk-factor-info">
                                        <h5>Va chạm</h5>
                                        <p>Rủi ro va chạm với các tàu khác dựa trên mật độ giao thông trong khu vực.</p>
                                    </div>
                                </div>
                                <div class="risk-factor-card">
                                    <div class="risk-factor-icon" style="background: #fd7e14;">W</div>
                                    <div class="risk-factor-info">
                                        <h5>Thời tiết</h5>
                                        <p>Rủi ro liên quan đến điều kiện thời tiết xấu như bão, sóng lớn, gió mạnh.</p>
                                    </div>
                                </div>
                                <div class="risk-factor-card">
                                    <div class="risk-factor-icon" style="background: #ffc107;">R</div>
                                    <div class="risk-factor-info">
                                        <h5>Lệch tuyến đường</h5>
                                        <p>Mức độ lệch khỏi tuyến đường thông thường hoặc đã đăng ký.</p>
                                    </div>
                                </div>
                                <div class="risk-factor-card">
                                    <div class="risk-factor-icon" style="background: #20c997;">S</div>
                                    <div class="risk-factor-info">
                                        <h5>Tốc độ bất thường</h5>
                                        <p>Tàu di chuyển quá nhanh hoặc quá chậm so với mức bình thường của loại tàu.</p>
                                    </div>
                                </div>
                                <div class="risk-factor-card">
                                    <div class="risk-factor-icon" style="background: #6f42c1;">N</div>
                                    <div class="risk-factor-info">
                                        <h5>Chướng ngại vật</h5>
                                        <p>Gần các chướng ngại vật hàng hải như đá ngầm, vùng nước nông, hoặc khu vực hạn chế.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="risk-results-panel">
                            <div id="risk-result" class="result-container"></div>
                            <div id="risk-map" style="height: 500px; width: 100%; border-radius: 10px; overflow: hidden; margin-top: 20px; display: none;"></div>
                        </div>
                    </div>
                </div>
                
                <script>
                    // Hiển thị thông báo nếu bản đồ không tải sau 3 giây
                    setTimeout(function() {
                        if (document.querySelector('#map iframe') && document.querySelector('#map iframe').contentDocument.body.innerHTML.includes('Make this Notebook Trusted')) {
                            document.getElementById('map-trust-message').style.display = 'block';
                        }
                    }, 3000);
                </script>
            </div>
        </div>
        
        <script>
            let isProcessing = false;
            
            async function downloadData() {
                if (isProcessing) return;
                
                const url = document.getElementById('aisUrl').value.trim();
                if (!url) {
                    showStatus('Please enter AIS data URL', 'error');
                    return;
                }
                
                isProcessing = true;
                document.getElementById('downloadBtn').innerHTML = '<span class="loading"></span> Processing...';
                showStatus('Downloading and processing data... This may take a few minutes.', 'info');
                
                try {
                    const response = await fetch('/download-ais', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: url})
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Download failed');
                    }
                    
                    const result = await response.json();
                    showStatus(`✅ Successfully processed ${result.total_records.toLocaleString()} records`, 'success');
                    showStats(result.stats);
                    await loadMap();
                } catch (error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                } finally {
                    isProcessing = false;
                    document.getElementById('downloadBtn').innerHTML = 'Download & Process';
                }
            }
            
            async function filterData() {
                const vesselTypes = Array.from(document.getElementById('vesselType').selectedOptions).map(o => o.value);
                const filters = {
                    vessel_types: vesselTypes.length > 0 ? vesselTypes : null,
                    min_lat: parseFloat(document.getElementById('minLat').value) || null,
                    max_lat: parseFloat(document.getElementById('maxLat').value) || null,
                    min_lon: parseFloat(document.getElementById('minLon').value) || null,
                    max_lon: parseFloat(document.getElementById('maxLon').value) || null
                };
                
                try {
                    showStatus('Applying filters...', 'info');
                    const response = await fetch('/filter-data', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(filters)
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Filter failed');
                    }
                    
                    const result = await response.json();
                    showStatus(`✅ Filtered to ${result.filtered_records.toLocaleString()} records`, 'success');
                    showStats(result.stats);
                    await loadMap();
                } catch (error) {
                    showStatus('❌ Error filtering data: ' + error.message, 'error');
                }
            }
            
            function clearFilters() {
                document.getElementById('vesselType').selectedIndex = -1;
                document.getElementById('minLat').value = '';
                document.getElementById('maxLat').value = '';
                document.getElementById('minLon').value = '';
                document.getElementById('maxLon').value = '';
                filterData();
            }
            
            async function exportData() {
                try {
                    showStatus('Preparing export...', 'info');
                    const response = await fetch('/export-data');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Export failed');
                    }
                    
                    const result = await response.json();
                    
                    // Create download link
                    const blob = new Blob([result.csv_data], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = result.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    showStatus('✅ Data exported successfully', 'success');
                } catch (error) {
                    showStatus('❌ Error exporting data: ' + error.message, 'error');
                }
            }
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = message;
                statusDiv.className = type;
            }
            
            function showStats(stats) {
                const statsHtml = `
                    <h3>📊 Data Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_vessels.toLocaleString()}</div>
                            <div>Total Vessels</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.vessel_types.length}</div>
                            <div>Vessel Types</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_records.toLocaleString()}</div>
                            <div>Total Records</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.time_span}</div>
                            <div>Time Span</div>
                        </div>
                    </div>
                    <p><strong>Vessel Types:</strong> ${stats.vessel_types.join(', ')}</p>
                    <p><strong>Date Range:</strong> ${stats.date_range.start} to ${stats.date_range.end}</p>
                    <p><strong>Geographic Bounds:</strong> Lat: ${stats.bounds[0].toFixed(3)} to ${stats.bounds[1].toFixed(3)}, Lon: ${stats.bounds[2].toFixed(3)} to ${stats.bounds[3].toFixed(3)}</p>
                `;
                document.getElementById('stats').innerHTML = statsHtml;
            }
            
            async function loadMap() {
                try {
                    showStatus('Generating map...', 'info');
                    const response = await fetch('/generate-map');
                    
                    if (!response.ok) {
                        throw new Error('Failed to generate map');
                    }
                    
                    const mapHtml = await response.text();
                    document.getElementById('map').innerHTML = mapHtml;
                    showStatus('✅ Map generated successfully', 'success');
                } catch (error) {
                    showStatus('❌ Error loading map: ' + error.message, 'error');
                }
            }
            
            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if (!fileInput.files || fileInput.files.length === 0) {
                    showStatus('Please select a file to upload', 'error');
                    return;
                }
                
                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    document.getElementById('uploadBtn').innerHTML = '<span class="loading"></span> Processing...';
                    showStatus(`Uploading and processing ${file.name}...`, 'info');
                    
                    const response = await fetch('/upload-file', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Upload failed');
                    }
                    
                    const result = await response.json();
                    showStatus(`✅ Successfully processed ${result.total_records.toLocaleString()} records from ${file.name}`, 'success');
                    showStats(result.stats);
                    await loadMap();
                } catch (error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                } finally {
                    document.getElementById('uploadBtn').innerHTML = 'Upload & Process';
                }
            }
            
            async function checkLocalData() {
                try {
                    showStatus('Checking for local data...', 'info');
                    
                    // Check data status
                    const response = await fetch('/data-status');
                    const status = await response.json();
                    
                    if (status.loaded) {
                        showStatus(`✅ Using local data with ${status.total_records.toLocaleString()} records`, 'success');
                        showStats(status.stats);
                        await loadMap();
                    } else {
                        showStatus('No data loaded. Please upload a file or generate sample data.', 'error');
                    }
                } catch (error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                }
            }
            
            async function generateSampleData() {
                try {
                    showStatus('Generating sample data...', 'info');
                    const response = await fetch('/generate-sample-data');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to generate sample data');
                    }
                    
                    const result = await response.json();
                    showStatus(`✅ Successfully generated ${result.total_records.toLocaleString()} sample records`, 'success');
                    showStats(result.stats);
                    await loadMap();
                } catch (error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                }
            }
            
            // Tab switching function
            function switchTab(tabId) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Deactivate all tab buttons
                document.querySelectorAll('.tab-button').forEach(button => {
                    button.classList.remove('active');
                });
                
                // Show selected tab content and activate button
                document.getElementById(`tab-content-${tabId}`).classList.add('active');
                document.getElementById(`tab-${tabId}`).classList.add('active');
            }
            
            // Load advanced map
            async function loadAdvancedMap() {
                try {
                    document.getElementById('advanced-map').innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ nâng cao...</div>';
                    
                    const response = await fetch('/advanced-map');
                    const mapHtml = await response.text();
                    
                    document.getElementById('advanced-map').innerHTML = mapHtml;
                } catch (error) {
                    document.getElementById('advanced-map').innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi khi tải bản đồ: ${error.message}</div>`;
                }
            }
            
            // Detect patterns
            async function detectPatterns() {
                try {
                    document.getElementById('patterns-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang phát hiện mẫu...</div>';
                    
                    const response = await fetch('/detect-patterns');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to detect patterns');
                    }
                    
                    const result = await response.json();
                    
                    let html = `<h4>Đã phát hiện ${result.n_clusters} cụm</h4>`;
                    html += `<p>Tổng số điểm: ${result.total_points}, Tỷ lệ nhiễu: ${(result.noise_ratio * 100).toFixed(2)}%</p>`;
                    
                    if (result.clusters && result.clusters.length > 0) {
                        html += '<h5>Các cụm lớn nhất:</h5><ul>';
                        
                        // Sắp xếp cụm theo kích thước giảm dần
                        const sortedClusters = [...result.clusters].sort((a, b) => b.points - a.points);
                        
                        // Hiển thị 5 cụm lớn nhất
                        for (let i = 0; i < Math.min(5, sortedClusters.length); i++) {
                            const cluster = sortedClusters[i];
                            html += `<li>Cụm ${cluster.id}: ${cluster.points} tàu, vị trí trung tâm: [${cluster.center[0].toFixed(4)}, ${cluster.center[1].toFixed(4)}]</li>`;
                        }
                        
                        html += '</ul>';
                    }
                    
                    document.getElementById('patterns-result').innerHTML = html;
                } catch (error) {
                    document.getElementById('patterns-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
                }
            }
            
            // Analyze vessel types
            async function analyzeVesselTypes() {
                try {
                    document.getElementById('vessel-types-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang phân tích loại tàu...</div>';
                    
                    const response = await fetch('/analyze-vessel-types');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to analyze vessel types');
                    }
                    
                    const result = await response.json();
                    
                    if ("error" in result) {
                        throw new Error(result.error);
                    }
                    
                    let html = '<div class="chart-container"><img src="data:image/png;base64,' + result.chart + '" alt="Vessel Types Chart"></div>';
                    
                    html += '<h4>Thống kê theo loại tàu:</h4><ul>';
                    
                    // Sắp xếp loại tàu theo số lượng giảm dần
                    const sortedTypes = Object.entries(result.vessel_counts).sort((a, b) => b[1] - a[1]);
                    
                    for (const [type, count] of sortedTypes) {
                        html += `<li>${type}: ${count} tàu`;
                        
                        // Thêm thông tin tốc độ nếu có
                        if (result.speed_stats && result.speed_stats[type]) {
                            const speed = result.speed_stats[type];
                            html += ` (Tốc độ trung bình: ${speed.avg_speed.toFixed(2)} knốt, tối đa: ${speed.max_speed.toFixed(2)} knốt)`;
                        }
                        
                        html += '</li>';
                    }
                    
                    html += '</ul>';
                    
                    document.getElementById('vessel-types-result').innerHTML = html;
                } catch (error) {
                    document.getElementById('vessel-types-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
                }
            }
            
            // Detect anomalies
            async function detectAnomalies() {
                try {
                    document.getElementById('anomalies-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang phát hiện dữ liệu bất thường...</div>';
                    
                    const response = await fetch('/detect-anomalies');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to detect anomalies');
                    }
                    
                    const result = await response.json();
                    
                    if ("error" in result) {
                        throw new Error(result.error);
                    }
                    
                    let html = `<h4>Đã phát hiện ${result.total_anomalies} dữ liệu bất thường (${(result.anomaly_ratio * 100).toFixed(2)}%)</h4>`;
                    
                    html += `<p>Ngưỡng tốc độ bất thường: < ${result.speed_threshold.lower.toFixed(2)} hoặc > ${result.speed_threshold.upper.toFixed(2)} knốt</p>`;
                    
                    if (result.anomaly_by_type) {
                        html += '<h5>Bất thường theo loại tàu:</h5><ul>';
                        
                        // Sắp xếp theo số lượng bất thường giảm dần
                        const sortedAnomalies = Object.entries(result.anomaly_by_type).sort((a, b) => b[1] - a[1]);
                        
                        for (const [type, count] of sortedAnomalies) {
                            html += `<li>${type}: ${count} tàu</li>`;
                        }
                        
                        html += '</ul>';
                    }
                    
                    document.getElementById('anomalies-result').innerHTML = html;
                } catch (error) {
                    document.getElementById('anomalies-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
                }
            }
            
            // Predict density
            async function predictDensity() {
                try {
                    document.getElementById('density-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang dự đoán mật độ...</div>';
                    
                    const response = await fetch('/predict-density');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to predict density');
                    }
                    
                    const result = await response.json();
                    
                    if ("error" in result) {
                        throw new Error(result.error);
                    }
                    
                    let html = `<h4>Dự đoán mật độ tàu thuyền</h4>`;
                    html += `<p>Mật độ trung bình: ${result.avg_density.toFixed(2)} tàu/ô lưới, Mật độ tối đa: ${result.max_density.toFixed(2)} tàu/ô lưới</p>`;
                    
                    if (result.high_density_areas && result.high_density_areas.length > 0) {
                        html += '<h5>Các khu vực có mật độ cao:</h5><ul>';
                        
                        // Sắp xếp theo mật độ giảm dần
                        const sortedAreas = [...result.high_density_areas].sort((a, b) => b.density - a.density);
                        
                        for (let i = 0; i < Math.min(5, sortedAreas.length); i++) {
                            const area = sortedAreas[i];
                            html += `<li>Khu vực [${area.center[0].toFixed(4)}, ${area.center[1].toFixed(4)}]: ${area.density.toFixed(2)} tàu</li>`;
                        }
                        
                        html += '</ul>';
                    }
                    
                    document.getElementById('density-result').innerHTML = html;
                } catch (error) {
                    document.getElementById('density-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
                }
            }
            
            // Extract hidden patterns
            async function extractHiddenPatterns() {
                try {
                    document.getElementById('hidden-result').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Đang khai phá dữ liệu ẩn...</div>';
                    
                    const response = await fetch('/extract-hidden-patterns');
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to extract hidden patterns');
                    }
                    
                    const result = await response.json();
                    
                    if ("error" in result) {
                        throw new Error(result.error);
                    }
                    
                    let html = `<h4>Đã phát hiện ${result.total_insights} thông tin ẩn</h4>`;
                    
                    if (result.insights && result.insights.length > 0) {
                        html += '<div class="insights-container">';
                        
                        for (const insight of result.insights) {
                            html += `<div class="insight-card">
                                <h5>${insight.description}</h5>
                                <p><strong>Loại phát hiện:</strong> ${getInsightTypeName(insight.type)}</p>
                            </div>`;
                        }
                        
                        html += '</div>';
                    } else {
                        html += '<p>Không tìm thấy thông tin ẩn nào trong dữ liệu.</p>';
                    }
                    
                    document.getElementById('hidden-result').innerHTML = html;
                } catch (error) {
                    document.getElementById('hidden-result').innerHTML = `<div style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${error.message}</div>`;
                }
            }
            
            // Load Marine Cadastre Map
            async function loadMarineCadastreMap() {
                try {
                    document.getElementById('marine-map').innerHTML = '<div style="text-align: center; padding: 50px;"><div class="loading"></div> Đang tải bản đồ Marine Cadastre...</div>';
                    
                    const response = await fetch('/marine-cadastre-map');
                    const mapHtml = await response.text();
                    
                    document.getElementById('marine-map').innerHTML = mapHtml;
                } catch (error) {
                    document.getElementById('marine-map').innerHTML = `<div style="text-align: center; padding: 50px; color: #dc3545;">Lỗi khi tải bản đồ: ${error.message}</div>`;
                }
            }
            
            // Risk analysis functions are now in /static/js/risk_analysis.js
            
            // Helper function to get insight type name
            function getInsightTypeName(type) {
                const typeNames = {
                    'geographic_hotspot': 'Khu vực tập trung cao',
                    'time_pattern': 'Mẫu thời gian',
                    'correlation': 'Tương quan giữa các biến',
                    'vessel_group': 'Nhóm tàu di chuyển cùng nhau'
                };
                
                return typeNames[type] || type;
            }
            
            // Sample URLs for testing
            window.onload = function() {
                const sampleUrl = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2023/AIS_2023_01_01.zip";
                document.getElementById('aisUrl').placeholder = "Example: " + sampleUrl;
                
                // Check if data is already loaded
                checkLocalData();
            }
        </script>
    </body>
    </html>
    """

@app.post("/download-ais")
async def download_ais_data(request: DownloadRequest):
    url = request.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        # Download data with timeout
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to download data: HTTP {response.status}")
                
                content = await response.read()
        
        # Process data based on file type
        df = None
        if url.endswith('.zip'):
            with zipfile.ZipFile(BytesIO(content)) as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                if not csv_files:
                    raise HTTPException(status_code=400, detail="No CSV files found in ZIP archive")
                
                # Read the first CSV file
                with zip_file.open(csv_files[0]) as csv_file:
                    df = pd.read_csv(csv_file, low_memory=False)
        elif url.endswith('.csv'):
            df = pd.read_csv(BytesIO(content), low_memory=False)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please provide CSV or ZIP file.")
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="No data found in the file")
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        # Store processed data
        processed_data['original'] = df
        processed_data['filtered'] = df.copy()
        
        # Generate statistics
        stats = generate_statistics(df)
        
        return {
            "total_records": len(df),
            "stats": stats,
            "message": "Data processed successfully"
        }
        
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The file appears to be empty or corrupted")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/data-status")
async def data_status():
    """
    Check if data is loaded and return basic statistics
    """
    if 'original' not in processed_data or processed_data['original'].empty:
        return {"loaded": False}
    
    df = processed_data['original']
    stats = generate_statistics(df)
    
    return {
        "loaded": True,
        "total_records": len(df),
        "stats": stats
    }

@app.post("/filter-data")
async def filter_data(filters: VesselFilter):
    if 'original' not in processed_data:
        raise HTTPException(status_code=400, detail="No data loaded. Please download data first.")
    
    df = processed_data['original'].copy()
    
    # Apply filters
    if filters.vessel_types:
        # Try different possible column names for vessel type
        vessel_col = None
        for col in ['VesselType', 'VesselName', 'ShipType', 'vessel_type']:
            if col in df.columns:
                vessel_col = col
                break
        
        if vessel_col:
            df = df[df[vessel_col].isin(filters.vessel_types)]
    
    # Apply geographic filters
    lat_col = None
    lon_col = None
    for col in ['LAT', 'Latitude', 'lat', 'latitude']:
        if col in df.columns:
            lat_col = col
            break
    for col in ['LON', 'Longitude', 'lon', 'longitude']:
        if col in df.columns:
            lon_col = col
            break
    
    if lat_col and lon_col:
        if filters.min_lat is not None:
            df = df[df[lat_col] >= filters.min_lat]
        if filters.max_lat is not None:
            df = df[df[lat_col] <= filters.max_lat]
        if filters.min_lon is not None:
            df = df[df[lon_col] >= filters.min_lon]
        if filters.max_lon is not None:
            df = df[df[lon_col] <= filters.max_lon]
    
    processed_data['filtered'] = df
    stats = generate_statistics(df)
    
    return {
        "filtered_records": len(df),
        "stats": stats
    }

@app.get("/generate-map")
async def generate_map():
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    
    if df.empty:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No data to display on map</h3><p>Try adjusting your filters or downloading new data.</p></div>"
    
    # Find coordinate columns
    lat_col = None
    lon_col = None
    for col in ['LAT', 'Latitude', 'lat', 'latitude']:
        if col in df.columns:
            lat_col = col
            break
    for col in ['LON', 'Longitude', 'lon', 'longitude']:
        if col in df.columns:
            lon_col = col
            break
    
    if not lat_col or not lon_col:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No coordinate data found</h3><p>The dataset doesn't contain recognizable latitude/longitude columns.</p></div>"
    
    # Remove invalid coordinates
    df_clean = df.dropna(subset=[lat_col, lon_col])
    df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
    df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
    
    if df_clean.empty:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No valid coordinates found</h3><p>All coordinate data appears to be invalid.</p></div>"
    
    # Create map centered on data
    center_lat = df_clean[lat_col].mean()
    center_lon = df_clean[lon_col].mean()
    
    # Thay vì sử dụng Folium, tạo bản đồ đơn giản bằng HTML và JavaScript (Leaflet)
    map_html = f'''
    <div id="vessel-map" style="height: 600px; width: 100%; border-radius: 10px;"></div>
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
            
            // Đợi Leaflet tải xong
            leafletJS.onload = function() {{
                initMap();
            }};
        }} else {{
            // Leaflet đã được tải, khởi tạo bản đồ ngay lập tức
            initMap();
        }}
        
        function initMap() {{
            // Tạo bản đồ
            var map = L.map('vessel-map').setView([{center_lat}, {center_lon}], 8);
            
            // Thêm lớp bản đồ nền
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(map);
            
            // Thêm các điểm tàu
            var points = [
    '''
    
    # Giới hạn số điểm để tránh quá tải
    max_points = min(500, len(df_clean))
    df_sample = df_clean.sample(n=max_points) if len(df_clean) > max_points else df_clean
    
    # Tìm cột loại tàu
    vessel_col = None
    for col in ['VesselType', 'VesselName', 'ShipType', 'vessel_type']:
        if col in df_clean.columns:
            vessel_col = col
            break
    
    # Thêm các điểm vào bản đồ
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
    map_html += ',\n                '.join(points_data)
    
    # Hoàn thành mã JavaScript
    map_html += '''
            ];
            
            // Màu sắc cho các loại tàu
            var vesselColors = {
                'Cargo': '#3388ff',
                'Tanker': '#dc3545',
                'Passenger': '#28a745',
                'Fishing': '#fd7e14',
                'Tug': '#6f42c1',
                'Military': '#000000',
                'Sailing': '#e83e8c',
                'Unknown': '#6c757d'
            };
            
            // Thêm các điểm vào bản đồ
            points.forEach(function(point) {
                var lat = point[0];
                var lon = point[1];
                var type = point[2];
                var popupText = point[3];
                
                var color = vesselColors[type] || vesselColors['Unknown'];
                
                L.circleMarker([lat, lon], {
                    radius: 5,
                    color: color,
                    fillColor: color,
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
                
                div.innerHTML = '<h4 style="margin-top: 0;">🚢 Loại tàu</h4>';
                
                // Thêm các loại tàu vào chú thích
                for (var type in vesselColors) {
                    div.innerHTML += 
                        '<div><span style="display:inline-block; width:15px; height:15px; border-radius:50%; background:' + 
                        vesselColors[type] + ';"></span> ' + type + '</div>';
                }
                
                return div;
            };
            legend.addTo(map);
        }}
    </script>
    '''
    
    return map_html
    
    # Define colors for different vessel types
    vessel_colors = {
        'Cargo': 'blue',
        'Tanker': 'red',
        'Passenger': 'green',
        'Fishing': 'orange',
        'Tug': 'purple',
        'Military': 'black',
        'Sailing': 'pink',
        'Unknown': 'gray'
    }
    
    # Find vessel type column
    vessel_col = None
    for col in ['VesselType', 'VesselName', 'ShipType', 'vessel_type']:
        if col in df_clean.columns:
            vessel_col = col
            break
    
    # Limit points for performance (sample if too many)
    max_points = 2000
    if len(df_clean) > max_points:
        df_sample = df_clean.sample(n=max_points)
    else:
        df_sample = df_clean
    
    # Add vessel points to map
    for _, row in df_sample.iterrows():
        vessel_type = row.get(vessel_col, 'Unknown') if vessel_col else 'Unknown'
        color = vessel_colors.get(vessel_type, 'gray')
        
        # Create popup text
        popup_text = f"<b>Position:</b> {row[lat_col]:.4f}, {row[lon_col]:.4f}<br>"
        if vessel_col:
            popup_text += f"<b>Type:</b> {vessel_type}<br>"
        
        # Add other available information
        for col in ['MMSI', 'VesselName', 'SOG', 'COG', 'BaseDateTime']:
            if col in row and pd.notna(row[col]):
                popup_text += f"<b>{col}:</b> {row[col]}<br>"
        
        folium.CircleMarker(
            location=[row[lat_col], row[lon_col]],
            radius=4,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; top: 10px; right: 10px; z-index: 1000; 
                background: white; padding: 15px; border: 2px solid grey; border-radius: 5px;
                font-family: Arial, sans-serif; font-size: 12px;">
    <h4 style="margin-top: 0;">🚢 Vessel Types</h4>
    '''
    
    for vessel_type, color in vessel_colors.items():
        if vessel_col and vessel_type in df_clean[vessel_col].values:
            legend_html += f'<p style="margin: 5px 0;"><span style="color: {color}; font-size: 16px;">●</span> {vessel_type}</p>'
    
    legend_html += f'<hr><p style="margin: 5px 0; font-size: 10px;">Showing {len(df_sample):,} of {len(df_clean):,} points</p></div>'
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Thêm script để đảm bảo bản đồ được hiển thị đúng cách
    map_html = m._repr_html_()
    trusted_html = f'''
    <div id="folium-map-container" style="height: 600px; width: 100%; border-radius: 10px; overflow: hidden;">
        {map_html}
    </div>
    <script>
        // Đánh dấu bản đồ là đáng tin cậy
        document.addEventListener('DOMContentLoaded', function() {{            
            // Thêm class để đánh dấu bản đồ đã được tin cậy
            var mapDiv = document.querySelector('#folium-map-container iframe');
            if (mapDiv) {{                
                mapDiv.setAttribute('sandbox', 'allow-scripts allow-same-origin');
            }}
        }});
    </script>
    '''
    
    return trusted_html

@app.get("/export-data")
async def export_data():
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to export")
    
    csv_data = df.to_csv(index=False)
    filename = f"ais_filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return {
        "csv_data": csv_data,
        "filename": filename
    }

@app.get("/detect-patterns")
async def detect_patterns():
    """Phát hiện mẫu di chuyển bất thường của tàu"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.detect_vessel_patterns(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/predict-density")
async def predict_density():
    """Dự đoán mật độ tàu thuyền trong khu vực"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.predict_vessel_density(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/analyze-vessel-types")
async def analyze_vessel_types():
    """Phân tích chi tiết theo loại tàu"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.analyze_vessel_types(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/advanced-map", response_class=HTMLResponse)
async def advanced_map():
    """Tạo bản đồ nâng cao với nhiều lớp dữ liệu"""
    if 'filtered' not in processed_data:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No data available</h3><p>Please load or generate data first.</p></div>"
    
    df = processed_data['filtered']
    if df.empty:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No data to display</h3><p>The filtered dataset is empty.</p></div>"
    
    return analytics.generate_advanced_map(df)

@app.get("/detect-anomalies")
async def detect_anomalies():
    """Phát hiện dữ liệu bất thường"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.detect_anomalies(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/analyze-correlations")
async def analyze_correlations_endpoint():
    """Phân tích tương quan giữa các biến"""
    return await api_endpoints.analyze_correlations(processed_data)

@app.get("/analyze-temporal-patterns")
async def analyze_temporal_patterns_endpoint():
    """Phân tích mẫu theo thời gian"""
    return await api_endpoints.analyze_temporal_patterns(processed_data)

@app.get("/detect-vessel-groups")
async def detect_vessel_groups_endpoint():
    """Phát hiện các nhóm tàu di chuyển cùng nhau"""
    return await api_endpoints.detect_vessel_groups(processed_data)

@app.get("/extract-hidden-patterns")
async def extract_hidden_patterns():
    """Khai phá các mẫu ẩn trong dữ liệu"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.extract_hidden_patterns(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.get("/calculate-risk-scores")
async def calculate_risk_scores():
    """Tính toán điểm rủi ro cho các tàu"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result_df = risk_analysis.calculate_risk_scores(df)
    if isinstance(result_df, dict) and "error" in result_df:
        raise HTTPException(status_code=400, detail=result_df["error"])
    
    # Lưu kết quả vào processed_data
    processed_data['risk_analyzed'] = result_df
    
    # Tạo thống kê rủi ro
    risk_stats = {
        "total_vessels": len(result_df),
        "high_risk": int(sum(result_df['RiskScore'] >= 70)),
        "medium_risk": int(sum((result_df['RiskScore'] >= 40) & (result_df['RiskScore'] < 70))),
        "low_risk": int(sum(result_df['RiskScore'] < 40)),
        "avg_risk_score": float(result_df['RiskScore'].mean()),
        "max_risk_score": float(result_df['RiskScore'].max()),
        "risk_factors": {
            "collision": float(result_df['CollisionRisk'].mean()),
            "weather": float(result_df['WeatherRisk'].mean()),
            "route": float(result_df['RouteDeviation'].mean()),
            "speed": float(result_df['SpeedAnomaly'].mean()),
            "navigation": float(result_df['NavigationHazard'].mean())
        }
    }
    
    return risk_stats

@app.post("/identify-risky-routes")
async def identify_risky_routes(risk_threshold: int = 70):
    """Xác định các hành trình có rủi ro cao"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    # Sử dụng dữ liệu đã phân tích rủi ro nếu có
    if 'risk_analyzed' in processed_data and not processed_data['risk_analyzed'].empty:
        df = processed_data['risk_analyzed']
    
    risky_routes = risk_analysis.identify_risky_routes(df, risk_threshold)
    if isinstance(risky_routes, dict) and "error" in risky_routes:
        raise HTTPException(status_code=400, detail=risky_routes["error"])
    
    return {
        "risky_routes": risky_routes,
        "total_routes": len(risky_routes),
        "risk_threshold": risk_threshold
    }

@app.get("/risk-map", response_class=HTMLResponse)
async def risk_map():
    """Tạo bản đồ hiển thị các khu vực có rủi ro cao"""
    if 'filtered' not in processed_data:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No data available</h3><p>Please load or generate data first.</p></div>"
    
    df = processed_data['filtered']
    if df.empty:
        return "<div style='text-align: center; padding: 50px; color: #666;'><h3>No data to display</h3><p>The filtered dataset is empty.</p></div>"
    
    # Sử dụng dữ liệu đã phân tích rủi ro nếu có
    if 'risk_analyzed' in processed_data and not processed_data['risk_analyzed'].empty:
        df = processed_data['risk_analyzed']
    
    return risk_analysis.generate_risk_map(df)

@app.get("/marine-cadastre-map", response_class=HTMLResponse)
async def marine_cadastre_map():
    """Tích hợp bản đồ từ marinecadastre.gov"""
    try:
        # Lấy dữ liệu từ processed_data để xác định vùng hiển thị
        if 'filtered' in processed_data and not processed_data['filtered'].empty:
            df = processed_data['filtered']
            
            # Tìm cột tọa độ
            lat_col = next((col for col in ['LAT', 'Latitude', 'lat', 'latitude'] if col in df.columns), None)
            lon_col = next((col for col in ['LON', 'Longitude', 'lon', 'longitude'] if col in df.columns), None)
            
            if lat_col and lon_col:
                # Lọc dữ liệu hợp lệ
                df_clean = df.dropna(subset=[lat_col, lon_col])
                df_clean = df_clean[(df_clean[lat_col] >= -90) & (df_clean[lat_col] <= 90)]
                df_clean = df_clean[(df_clean[lon_col] >= -180) & (df_clean[lon_col] <= 180)]
                
                if not df_clean.empty:
                    # Tính toán vùng hiển thị
                    min_lat = df_clean[lat_col].min()
                    max_lat = df_clean[lat_col].max()
                    min_lon = df_clean[lon_col].min()
                    max_lon = df_clean[lon_col].max()
                    center_lat = df_clean[lat_col].mean()
                    center_lon = df_clean[lon_col].mean()
                else:
                    # Giá trị mặc định nếu không có dữ liệu hợp lệ
                    center_lat = 25.0
                    center_lon = -90.0
                    min_lat = center_lat - 5
                    max_lat = center_lat + 5
                    min_lon = center_lon - 5
                    max_lon = center_lon + 5
            else:
                # Giá trị mặc định nếu không tìm thấy cột tọa độ
                center_lat = 25.0
                center_lon = -90.0
                min_lat = center_lat - 5
                max_lat = center_lat + 5
                min_lon = center_lon - 5
                max_lon = center_lon + 5
        else:
            # Giá trị mặc định nếu không có dữ liệu
            center_lat = 25.0
            center_lon = -90.0
            min_lat = center_lat - 5
            max_lat = center_lat + 5
            min_lon = center_lon - 5
            max_lon = center_lon + 5
        
        # Tạo HTML để nhúng bản đồ từ marinecadastre.gov
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Marine Cadastre AIS Map</title>
            <meta charset="UTF-8">
            <style>
                body, html {{ margin: 0; padding: 0; height: 100%; overflow: hidden; }}
                #map-container {{ width: 100%; height: 600px; border: none; }}
                .map-overlay {{ 
                    position: absolute; 
                    bottom: 20px; 
                    right: 20px; 
                    background: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    box-shadow: 0 0 10px rgba(0,0,0,0.2); 
                    z-index: 1000; 
                }}
                .map-title {{ 
                    position: absolute; 
                    top: 10px; 
                    left: 50%; 
                    transform: translateX(-50%); 
                    background: rgba(255,255,255,0.8); 
                    padding: 5px 15px; 
                    border-radius: 20px; 
                    font-weight: bold; 
                    z-index: 1000; 
                }}
            </style>
        </head>
        <body>
            <div class="map-title">Marine Cadastre AIS Data Viewer</div>
            <iframe id="map-container" 
                src="https://marinecadastre.gov/nationalviewer/?utm_source=external" 
                width="100%" height="600" frameborder="0" allowfullscreen>
            </iframe>
            <div class="map-overlay">
                <strong>Vùng dữ liệu hiện tại:</strong><br>
                Vĩ độ: {min_lat:.4f} đến {max_lat:.4f}<br>
                Kinh độ: {min_lon:.4f} đến {max_lon:.4f}
            </div>
            
            <script>
                // Hàm để điều khiển bản đồ sau khi nó đã tải
                function setupMap() {{
                    try {{
                        // Cố gắng truy cập iframe và điều khiển bản đồ
                        const iframe = document.getElementById('map-container');
                        // Có thể thêm mã để tương tác với bản đồ trong iframe nếu API cho phép
                    }} catch (error) {{
                        console.error('Không thể điều khiển bản đồ:', error);
                    }}
                }}
                
                // Chờ iframe tải xong
                document.getElementById('map-container').onload = setupMap;
            </script>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        return f"<div>Lỗi khi tạo bản đồ Marine Cadastre: {str(e)}</div>"

def generate_statistics(df):
    if df.empty:
        return {
            "total_vessels": 0,
            "total_records": 0,
            "vessel_types": [],
            "date_range": {"start": "N/A", "end": "N/A"},
            "bounds": [0, 0, 0, 0],
            "time_span": "N/A"
        }
    
    # Find relevant columns
    mmsi_col = None
    vessel_col = None
    date_col = None
    lat_col = None
    lon_col = None
    
    for col in ['MMSI', 'mmsi', 'VesselId']:
        if col in df.columns:
            mmsi_col = col
            break
    
    for col in ['VesselType', 'VesselName', 'ShipType', 'vessel_type']:
        if col in df.columns:
            vessel_col = col
            break
    
    for col in ['BaseDateTime', 'DateTime', 'Timestamp', 'date_time']:
        if col in df.columns:
            date_col = col
            break
    
    for col in ['LAT', 'Latitude', 'lat', 'latitude']:
        if col in df.columns:
            lat_col = col
            break
    
    for col in ['LON', 'Longitude', 'lon', 'longitude']:
        if col in df.columns:
            lon_col = col
            break
    
    # Calculate statistics
    total_vessels = len(df[mmsi_col].unique()) if mmsi_col else len(df)
    vessel_types = df[vessel_col].unique().tolist() if vessel_col else []
    
    # Date range
    date_start = date_end = "N/A"
    time_span = "N/A"
    if date_col:
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if not dates.empty:
                date_start = dates.min().strftime('%Y-%m-%d %H:%M')
                date_end = dates.max().strftime('%Y-%m-%d %H:%M')
                time_span = str(dates.max() - dates.min()).split('.')[0]  # Remove microseconds
        except:
            pass
    
    # Geographic bounds
    bounds = [0, 0, 0, 0]
    if lat_col and lon_col:
        try:
            lat_data = pd.to_numeric(df[lat_col], errors='coerce').dropna()
            lon_data = pd.to_numeric(df[lon_col], errors='coerce').dropna()
            if not lat_data.empty and not lon_data.empty:
                bounds = [
                    float(lat_data.min()), float(lat_data.max()),
                    float(lon_data.min()), float(lon_data.max())
                ]
        except:
            pass
    
    return {
        "total_vessels": total_vessels,
        "total_records": len(df),
        "vessel_types": [str(vt) for vt in vessel_types if pd.notna(vt)],
        "date_range": {
            "start": date_start,
            "end": date_end
        },
        "bounds": bounds,
        "time_span": time_span
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)