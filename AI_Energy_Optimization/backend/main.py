from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import joblib
import os
from typing import List, Dict
from pydantic import BaseModel
import datetime

app = FastAPI(title="Voltix Energy API")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Load Model
try:
    model_path = os.path.join(MODELS_DIR, 'energy_forecast_model.pkl')
    model = joblib.load(model_path)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Helper to load data
def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    return pd.read_csv(path)

@app.get("/")
def read_root():
    return {"message": "Welcome to Voltix Energy API"}

@app.get("/api/buildings")
def get_buildings():
    df = load_csv("buildings.csv")
    return df.to_dict(orient="records")

@app.get("/api/dashboard-data")
def get_dashboard_data(building_id: str):
    # Load all data
    df_energy = load_csv("energy_readings.csv")
    df_weather = load_csv("weather_data.csv")
    df_occupancy = load_csv("occupancy_data.csv")
    df_buildings = load_csv("buildings.csv")
    
    # Process timestamps
    df_energy['timestamp'] = pd.to_datetime(df_energy['timestamp'])
    df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])
    df_occupancy['timestamp'] = pd.to_datetime(df_occupancy['timestamp'])
    
    # Filter for building
    df_energy = df_energy[df_energy['building_id'] == building_id]
    df_occupancy = df_occupancy[df_occupancy['building_id'] == building_id]
    
    # Merge
    main_df = df_energy.merge(df_weather, on='timestamp')
    main_df = main_df.merge(df_occupancy, on=['timestamp', 'building_id'])
    
    # Get metadata
    meta = df_buildings[df_buildings['building_id'] == building_id].iloc[0].to_dict()
    
    # Prepare features for prediction
    main_df['occupancy_code'] = main_df['occupancy_level'].map({'Low': 0, 'Medium': 1, 'High': 2})
    main_df['building_type_code'] = meta['building_type'] # This needs to be encoded similarly to training time
    
    # Re-encoding building type to match training logic (which used cat.codes)
    # Ideally we should save the encoder. For now, we will map manually based on training data knowledge:
    # 'Academic', 'Hostel', 'Office'. (A=0, H=1, O=2 likely due to alpha sort)
    # Let's fix this robustly by loading all buildings and creating the map
    
    all_b_types = df_buildings['building_type'].astype('category').cat.categories
    b_type_map = {k: v for v, k in enumerate(sorted(df_buildings['building_type'].unique()))}
    
    main_df['building_type_code'] = b_type_map.get(meta['building_type'], 0)
    
    main_df['hour'] = main_df['timestamp'].dt.hour
    main_df['day_of_week'] = main_df['timestamp'].dt.dayofweek
    main_df['is_weekend'] = main_df['day_of_week'] >= 5
    
    features = ['building_type_code', 'area_sq_m', 'temperature', 'humidity', 
                'occupancy_code', 'hour', 'day_of_week', 'is_weekend']
    
    # Inject area
    main_df['area_sq_m'] = meta['area_sq_m']
    
    # Predict
    if model:
        main_df['predicted_kwh'] = model.predict(main_df[features])
    else:
        main_df['predicted_kwh'] = 0
        
    # Get latest status
    latest = main_df.iloc[-1]
    
    # Recommendations Logic
    recommendations = []
    if latest['occupancy_level'] == 'Low':
        recommendations.append({
            "action": "Increase HVAC setpoint by 1.5°C",
            "impact": "Estimated 10% energy savings",
            "comfort": "Minimal impact (Low Occupancy)"
        })
    
    if latest['temperature'] < 20 and latest['energy_kwh'] > 50:
        recommendations.append({
            "action": "Check Window Insulation",
            "impact": "Reduce heating load",
            "comfort": "High (Draft prevention)"
        })
        
    if not recommendations:
        recommendations.append({
            "action": "No specific action needed",
            "impact": "System optimal",
            "comfort": "Good"
        })

    # Limit historical data to last 100 points for chart performance
    chart_data = main_df.tail(100)[['timestamp', 'energy_kwh', 'predicted_kwh']].to_dict(orient="records")
    
    # Calculate Real AI Confidence (R² Score for this building)
    # This shows how well the model fits this specific building's data
    try:
        if len(main_df) > 0:
            y_true = main_df['energy_kwh']
            y_pred = main_df['predicted_kwh']
            # Simple R2 calculation manually to avoid overhead or if model.score isn't ideal
            # R2 = 1 - (SS_res / SS_tot)
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            r2_score = 1 - (ss_res / ss_tot)
            confidence = max(0, min(100, int(r2_score * 100))) # Clamp between 0-100
        else:
            confidence = 0
            
        # Model 2: Wastage Detection Logic
        # Flag if Actual > Predicted * 1.2 (20% excess)
        if len(main_df) > 0:
            last_actual = latest['energy_kwh']
            last_pred = latest['predicted_kwh']
            if last_pred > 0 and last_actual > (last_pred * 1.2):
                recommendations.insert(0, {
                    "action": "⚠️ CRITICAL WASTAGE DETECTED",
                    "impact": f"Usage is {int((last_actual/last_pred - 1)*100)}% above AI forecast!",
                    "comfort": "Check equipment immediately"
                })
    except Exception as e:
        print(f"Error calculating confidence: {e}")
        confidence = 0

    return {
        "building_meta": meta, # Assuming meta is already dict of python types
        "current_status": {
            "energy_kwh": float(round(latest['energy_kwh'], 2)),
            "occupancy": str(latest['occupancy_level']),
            "temperature": float(round(latest['temperature'], 1)),
            "humidity": float(round(latest['humidity'], 1))
        },
        "chart_data": chart_data,
        "recommendations": recommendations,
        "total_kwh_month": float(round(main_df['energy_kwh'].sum(), 2)),
        "co2_emissions": float(round(main_df['energy_kwh'].sum() * 0.85, 2)),
        "ai_confidence": int(confidence)
    }

class SimulationRequest(BaseModel):
    building_type: str
    area_sq_m: float
    temperature: float
    humidity: float
    occupancy_level: str  # Low, Medium, High
    hour: int
    day_of_week: int

@app.post("/api/simulate")
def simulate_energy(req: SimulationRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
        
    # Process Inputs
    occupancy_map = {'Low': 0, 'Medium': 1, 'High': 2}
    # Building Type Map (Need to ensure this matches training)
    # Hardcoding based on known types for simplicity, or we could load from CSV dynamically
    b_type_map = {'Academic': 0, 'Hostel': 1, 'Office': 2} 
    
    # Prepare vector
    # ['building_type_code', 'area_sq_m', 'temperature', 'humidity', 'occupancy_code', 'hour', 'day_of_week', 'is_weekend']
    
    b_code = b_type_map.get(req.building_type, 0)
    occ_code = occupancy_map.get(req.occupancy_level, 0)
    is_weekend = 1 if req.day_of_week >= 5 else 0
    
    features = pd.DataFrame([{
        'building_type_code': b_code,
        'area_sq_m': req.area_sq_m,
        'temperature': req.temperature,
        'humidity': req.humidity,
        'occupancy_code': occ_code,
        'hour': req.hour,
        'day_of_week': req.day_of_week,
        'is_weekend': is_weekend
    }])
    
    predicted_kwh = model.predict(features)[0]
    
    # Generate recommendations based on simulated state
    recs = []
    if req.occupancy_level == 'Low' and predicted_kwh > 20: 
         recs.append("Reduce HVAC setpoint (Simulated)")
         
    return {
        "predicted_kwh": float(round(predicted_kwh, 2)),
        "recommendations": recs
    }

class FuturePredictionRequest(BaseModel):
    building_id: str
    target_time: str # ISO format datetime

@app.post("/api/predict-future")
def predict_future(req: FuturePredictionRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
        
    try:
        dt = pd.to_datetime(req.target_time)
    except:
        raise HTTPException(status_code=400, detail="Invalid Date Format")
        
    hour = dt.hour
    day_of_week = dt.dayofweek
    is_weekend = 1 if day_of_week >= 5 else 0
    
    # Estimate Weather (Simple Heuristic for Demo)
    # Assume 24C base, +/- 5C daily cycle
    est_temp = 24 + 5 * np.sin((hour - 6) * 2 * np.pi / 24)
    est_humidity = 50
    
    # Estimate Occupancy (Heuristic)
    # Offices: High 9-17 Mon-Fri
    occupancy_code = 0 # Low
    if 9 <= hour <= 17 and not is_weekend:
        occupancy_code = 2 # High
    elif 8 <= hour <= 20:
        occupancy_code = 1 # Medium
        
    df = load_csv("buildings.csv")
    meta = df[df['building_id'] == req.building_id].iloc[0]
    
    # Reconstruct Map
    all_b_types = sorted(df['building_type'].unique())
    b_type_map = {k: v for v, k in enumerate(all_b_types)}
    b_code = b_type_map.get(meta['building_type'], 0)
    
    features = pd.DataFrame([{
        'building_type_code': b_code,
        'area_sq_m': meta['area_sq_m'],
        'temperature': est_temp,
        'humidity': est_humidity,
        'occupancy_code': occupancy_code,
        'hour': hour,
        'day_of_week': day_of_week,
        'is_weekend': is_weekend
    }])
    
    pred_kwh = model.predict(features)[0]
    
    # Future Recommendations
    recs = []
    if pred_kwh > 20:
        recs.append("Schedule Pre-cooling")
    if is_weekend and pred_kwh > 5:
        recs.append("Verify Weekend Shutdown")
        
    return {
        "predicted_kwh": float(round(pred_kwh, 2)),
        "estimated_temp": float(round(est_temp, 1)),
        "occupancy_est": ["Low", "Medium", "High"][occupancy_code],
        "recommendations": recs
    }

# Gemini Integration
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GENAI_KEY = os.getenv("GEMINI_API_KEY")

if GENAI_KEY:
    try:
        genai.configure(api_key=GENAI_KEY)
        # Try to initialize with Flash, fallback to Pro if needed (though Pro is deprecated)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {e}")
        gemini_model = None
else:
    gemini_model = None

class ChatRequest(BaseModel):
    message: str
    context: Dict  # Will contain current metrics like energy, temp, etc.

@app.post("/api/chat")
async def chat_with_advisor(req: ChatRequest):
    if not gemini_model:
        raise HTTPException(status_code=503, detail="Gemini API Key not configured")
    
    # Construct Contextual Prompt
    metrics = req.context
    
    # Load Master Prompt
    try:
        prompt_path = os.path.join(BASE_DIR, 'prompts', 'energy_advisor_prompt.txt')
        with open(prompt_path, 'r') as f:
             master_prompt = f.read()
    except:
        master_prompt = "You are a helpful energy advisor."

    prompt = f"""
    {master_prompt}

    ---
    CURRENT CONTEXT:
    User Input: "{req.message}"
    Building Context:
    - Type: {metrics.get('building_type', 'Unknown')}
    - Energy: {metrics.get('energy_kwh', 0)} kWh
    - Occupancy: {metrics.get('occupancy', 'Unknown')}
    - Temperature: {metrics.get('temperature', 0)}°C
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini Error: {e}")
        raise HTTPException(status_code=500, detail="AI Service Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
