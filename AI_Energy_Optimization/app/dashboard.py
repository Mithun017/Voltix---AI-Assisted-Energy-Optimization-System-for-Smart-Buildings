import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import os

# Page Config
st.set_page_config(page_title="Voltix Energy Intelligence", layout="wide")

# Load Data & Model
@st.cache_data
def load_data():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    buildings = pd.read_csv(os.path.join(base_path, 'data/buildings.csv'))
    weather = pd.read_csv(os.path.join(base_path, 'data/weather_data.csv'))
    occupancy = pd.read_csv(os.path.join(base_path, 'data/occupancy_data.csv'))
    energy = pd.read_csv(os.path.join(base_path, 'data/energy_readings.csv'))
    
    # Process timestamps - handle different formats or just fallback to generic
    weather['timestamp'] = pd.to_datetime(weather['timestamp'])
    occupancy['timestamp'] = pd.to_datetime(occupancy['timestamp'])
    energy['timestamp'] = pd.to_datetime(energy['timestamp'])
    
    # Merge
    main_df = energy.merge(weather, on='timestamp')
    main_df = main_df.merge(occupancy, on=['timestamp', 'building_id'])
    main_df = main_df.merge(buildings, on='building_id')
    
    return main_df, buildings

@st.cache_resource
def load_model():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, 'models/energy_forecast_model.pkl')
    return joblib.load(model_path)

try:
    df, buildings_ref = load_data()
    model = load_model()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar
st.sidebar.title("Voltix Control Panel")
selected_building = st.sidebar.selectbox("Select Building", buildings_ref['building_id'].unique())

# Filter data for selected building
building_df = df[df['building_id'] == selected_building].copy()
building_meta = buildings_ref[buildings_ref['building_id'] == selected_building].iloc[0]

# --- Main Dashboard ---
st.title(f"🏢 Building {selected_building} - Energy Intelligence")

# 1. KPI Row (Simulating 'Current' Status as the last available record)
latest = building_df.iloc[-1]
st.markdown("### 📊 Real-Time Status")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Usage", f"{latest['energy_kwh']:.2f} kWh", delta_color="inverse")
with col2:
    st.metric("Occupancy", latest['occupancy_level'])
with col3:
    st.metric("Temperature", f"{latest['temperature']:.1f} °C")
with col4:
    st.metric("Humidity", f"{latest['humidity']:.1f} %")

st.markdown("---")

# 2. Forecasting & Analysis
st.markdown("### 📈 Energy Consumption & Forecast")

# Prepare features for prediction on the whole dataset (for visualization)
building_df['occupancy_code'] = building_df['occupancy_level'].map({'Low': 0, 'Medium': 1, 'High': 2})
building_df['building_type_code'] = building_df['building_type'].astype('category').cat.codes
building_df['hour'] = building_df['timestamp'].dt.hour
building_df['day_of_week'] = building_df['timestamp'].dt.dayofweek
building_df['is_weekend'] = building_df['day_of_week'] >= 5

features = ['building_type_code', 'area_sq_m', 'temperature', 'humidity', 
            'occupancy_code', 'hour', 'day_of_week', 'is_weekend']
            
building_df['predicted_kwh'] = model.predict(building_df[features])

# Plotting
fig = go.Figure()
fig.add_trace(go.Scatter(x=building_df['timestamp'], y=building_df['energy_kwh'], name='Actual Usage', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=building_df['timestamp'], y=building_df['predicted_kwh'], name='Predicted (AI)', line=dict(color='orange', dash='dot')))
fig.update_layout(title="Actual vs Predicted Energy Usage", xaxis_title="Time", yaxis_title="Energy (kWh)")
st.plotly_chart(fig, use_container_width=True)

# 3. Wastage Detection
st.markdown("### 🚨 Wastage Detection")
building_df['deviation'] = building_df['energy_kwh'] - building_df['predicted_kwh']
building_df['deviation_pct'] = (building_df['deviation'] / building_df['predicted_kwh']) * 100
wastage = building_df[building_df['deviation_pct'] > 20]

if not wastage.empty:
    st.warning(f"Detected {len(wastage)} hourly intervals with abnormal energy usage (>20% deviation).")
    st.dataframe(wastage[['timestamp', 'energy_kwh', 'predicted_kwh', 'deviation_pct']].tail(5))
else:
    st.success("No significant energy wastage detected recently.")

# 4. Optimization Recommendations
st.markdown("### 💡 AI Recommendations")

# Simple logic based on latest state
rec_col1, rec_col2 = st.columns(2)

recommendations = []
if latest['occupancy_level'] == 'Low':
    recommendations.append("📉 **Action:** Increase HVAC setpoint by 1.5°C.")
    recommendations.append("💰 **Impact:** Estimated 10% energy savings.")
    recommendations.append("✅ **Comfort:** minimal impact due to low occupancy.")

if latest['temperature'] < 20 and latest['energy_kwh'] > 50:
    recommendations.append("⚠️ **Wastage Alert:** Heating load is high. Check window insulation.")

if not recommendations:
    recommendations.append("✅ System is operating optimally.")

with rec_col1:
    st.info("\n\n".join(recommendations))

# 5. Sustainability
st.markdown("### 🌱 Sustainability Impact")
total_kwh = building_df['energy_kwh'].sum()
# Assuming 0.85 kg CO2 per kWh (approx for coal-heavy grid)
co2_emissions = total_kwh * 0.85 

st.write(f"**Total Energy Consumed (Month):** {total_kwh:,.2f} kWh")
st.write(f"**Estimated CO₂ Footprint:** {co2_emissions:,.2f} kg")

if st.button("Generate Optimization Report"):
    st.success("Report generated successfully! (Mock capability)")
