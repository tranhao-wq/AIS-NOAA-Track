import uvicorn
import os

if __name__ == "__main__":
    print("[INFO] Starting AIS Data Analyzer...")
    print("[INFO] Access the application at: http://localhost:8000")
    print("[INFO] Features:")
    print("   - Download AIS data from marinecadastre.gov")
    print("   - Interactive filtering and visualization")
    print("   - Export filtered data to CSV")
    print("   - Real-time map with vessel positions")
    print("   - Advanced analytics and pattern detection")
    print("   - Vessel density prediction")
    print("   - Hidden pattern extraction")
    
    # Check for sample data
    sample_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'AIS_sample_data.csv')
    if os.path.exists(sample_data_path):
        print("\n[INFO] Sample data found: " + sample_data_path)
        print("[INFO] The application will automatically load this data on startup")
    
    print("\n[INFO] Starting server...")
    
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )