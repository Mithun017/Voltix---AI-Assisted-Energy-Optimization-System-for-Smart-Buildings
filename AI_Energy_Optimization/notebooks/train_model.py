import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os

# Robust path handling
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
models_dir = os.path.join(base_dir, 'models')
os.makedirs(models_dir, exist_ok=True)

print(f"Loading data from: {data_dir}")
print(f"Saving models to: {models_dir}")

# Load data
df_buildings = pd.read_csv(os.path.join(data_dir, 'buildings.csv'))
df_weather = pd.read_csv(os.path.join(data_dir, 'weather_data.csv'))
df_occupancy = pd.read_csv(os.path.join(data_dir, 'occupancy_data.csv'))
df_energy = pd.read_csv(os.path.join(data_dir, 'energy_readings.csv'))

# Date conversions
df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])
df_occupancy['timestamp'] = pd.to_datetime(df_occupancy['timestamp'])
df_energy['timestamp'] = pd.to_datetime(df_energy['timestamp'])

# Merge
df_main = df_energy.merge(df_weather, on='timestamp')
df_main = df_main.merge(df_occupancy, on=['timestamp', 'building_id'])
df_main = df_main.merge(df_buildings, on='building_id')

print(f"Data loaded. Shape: {df_main.shape}")

# Feature Engineering
df_main['occupancy_code'] = df_main['occupancy_level'].map({'Low': 0, 'Medium': 1, 'High': 2})
df_main['building_type_code'] = df_main['building_type'].astype('category').cat.codes

df_main['hour'] = df_main['timestamp'].dt.hour
df_main['day_of_week'] = df_main['timestamp'].dt.dayofweek
df_main['is_weekend'] = df_main['day_of_week'] >= 5

features = ['building_type_code', 'area_sq_m', 'temperature', 'humidity', 
            'occupancy_code', 'hour', 'day_of_week', 'is_weekend']
target = 'energy_kwh'

X = df_main[features]
y = df_main[target]

# Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Random Forest Model...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"Mean Absolute Error: {mae:.2f} kWh")

# Save
joblib.dump(model, os.path.join(models_dir, 'energy_forecast_model.pkl'))
print("Model saved to models/energy_forecast_model.pkl")
