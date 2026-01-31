import pandas as pd
import numpy as np
from datetime import datetime
import os

# Robust path handling
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

# Configuration
NUM_BUILDINGS = 5
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 2, 1)
date_range = pd.date_range(start=START_DATE, end=END_DATE, freq='h')[:-1]
n_timestamps = len(date_range)

# 1. Buildings
building_types = ['Academic', 'Hostel', 'Office']
hvac_types = ['Split AC', 'Central Chiller', 'VRF']
buildings = []
for i in range(1, NUM_BUILDINGS + 1):
    b_type = building_types[i % len(building_types)]
    area = {'Academic': np.random.randint(2000, 5000), 'Hostel': np.random.randint(3000, 8000), 'Office': np.random.randint(1000, 3000)}[b_type]
    buildings.append({'building_id': f'B{i:03d}', 'building_type': b_type, 'area_sq_m': area, 'hvac_type': np.random.choice(hvac_types)})

df_buildings = pd.DataFrame(buildings)
df_buildings.to_csv(os.path.join(data_dir, 'buildings.csv'), index=False)

# 2. Weather
hour_of_day = date_range.hour
temp_variation = 5 * np.sin((hour_of_day - 6) * 2 * np.pi / 24)
temperatures = 24 + temp_variation + np.random.normal(0, 1, n_timestamps)
humidity = np.clip(60 - 1.5 * temp_variation + np.random.normal(0, 5, n_timestamps), 30, 90)
df_weather = pd.DataFrame({'timestamp': date_range, 'temperature': temperatures, 'humidity': humidity})
df_weather.to_csv(os.path.join(data_dir, 'weather_data.csv'), index=False)

# 3. Occupancy
occupancy_records = []
for _, b in df_buildings.iterrows():
    for ts in date_range:
        hour, weekday = ts.hour, ts.weekday() < 5
        level = 'Low'
        if b['building_type'] == 'Office' and weekday and 9 <= hour <= 18: level = 'High' if 10 <= hour <= 16 else 'Medium'
        elif b['building_type'] == 'Academic' and weekday and 8 <= hour <= 17: level = 'High' if 9 <= hour <= 15 else 'Medium'
        elif b['building_type'] == 'Hostel':
            if 22 <= hour or hour <= 7: level = 'High'
            elif not (weekday and 9 <= hour <= 17): level = 'Medium'
        occupancy_records.append({'timestamp': ts, 'building_id': b['building_id'], 'occupancy_level': level})

df_occupancy = pd.DataFrame(occupancy_records)
df_occupancy.to_csv(os.path.join(data_dir, 'occupancy_data.csv'), index=False)

# 4. Energy (Vectorized Refactoring)
df_energy = df_occupancy.merge(df_weather, on='timestamp').merge(df_buildings, on='building_id')
occ_map = {'Low': 0.5, 'Medium': 1.0, 'High': 1.5}
df_energy['occ_mult'] = df_energy['occupancy_level'].map(occ_map)

# Non-linear temp impact & Noise
temp_diff = df_energy['temperature'] - 24
df_energy['temp_mult'] = np.where(temp_diff > 0, 1 + (temp_diff * 0.1), 1 + (np.abs(temp_diff) * 0.02))
noise = np.random.normal(1, 0.03, len(df_energy))
noise *= np.where(np.random.rand(len(df_energy)) < 0.01, 1.1, 1.0)

df_energy['energy_kwh'] = (df_energy['area_sq_m'] * 0.002 * df_energy['occ_mult'] * df_energy['temp_mult'] * noise).round(2)
df_energy[['timestamp', 'building_id', 'energy_kwh']].to_csv(os.path.join(data_dir, 'energy_readings.csv'), index=False)
print("Data generation complete.")
