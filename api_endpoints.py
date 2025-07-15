from fastapi import HTTPException
import analytics

# API endpoints for advanced analytics

async def analyze_correlations(processed_data):
    """Phân tích tương quan giữa các biến"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.analyze_correlations(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

async def analyze_temporal_patterns(processed_data):
    """Phân tích mẫu theo thời gian"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.analyze_temporal_patterns(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

async def detect_vessel_groups(processed_data):
    """Phát hiện các nhóm tàu di chuyển cùng nhau"""
    if 'filtered' not in processed_data:
        raise HTTPException(status_code=400, detail="No data available")
    
    df = processed_data['filtered']
    if df.empty:
        raise HTTPException(status_code=400, detail="No data to analyze")
    
    result = analytics.detect_vessel_groups(df)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result