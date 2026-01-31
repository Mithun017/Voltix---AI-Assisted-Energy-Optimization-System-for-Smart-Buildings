# ⚡ Voltix AI: AI-Assisted Energy Optimization System for Smart Buildings

## 📖 Project Overview
Voltix AI is an intelligent energy management dashboard designed for smart buildings. It leverages **Machine Learning (Random Forest)** to forecast energy consumption and **Generative AI (Google Gemini)** to act as an intelligent energy advisor. The system helps facility managers reduce energy wastage, optimize HVAC settings, and visualize consumption patterns in real-time.

---

## 🛠️ Tech Stack

### **Frontend (User Interface)**
*   **Framework**: React (Vite)
*   **Styling**: Glassmorphism CSS, Responsive Grid
*   **Charts**: Recharts (Interactive Line/Bar charts)
*   **State Management**: React Hooks

### **Backend (API & Logic)**
*   **Framework**: FastAPI (Python)
*   **Server**: Uvicorn (ASGI)
*   **Data Processing**: Pandas, NumPy
*   **AI Integration**: `google-generativeai` (Gemini 1.5 Flash)

### **Machine Learning (Core Engine)**
*   **Algorithm**: Random Forest Regressor (`sklearn`)
*   **Accuracy**: ~99% (MAE: 0.30 kWh)
*   **Model Storage**: `joblib` (.pkl format)

---

## 📂 Project Structure

```text
47.AI-Assisted Energy Optimization System.../
├── AI_Energy_Optimization/         # Main Source Code
│   ├── backend/                    # FastAPI Server
│   │   ├── main.py                 # API Endpoints (Predict, Simulate, Chat)
│   │   ├── check_model.py          # Diagnostic Script
│   │   └── requirements.txt        # Python Dependencies
│   │
│   ├── frontend/                   # React Dashboard
│   │   ├── src/                    # UI Components (App.jsx, App.css)
│   │   ├── package.json            # Node Dependencies
│   │   └── vite.config.js          # Build Config
│   │
│   ├── data/                       # Datasets
│   │   ├── buildings.csv           # Building Metadata
│   │   ├── energy_readings.csv     # Historical Consumption
│   │   ├── weather_data.csv        # Temperature/Humidity Logs
│   │   └── wastage_anomalies.csv   # AI Detected Wastage Report
│   │
│   ├── models/                     # Trained AI Models
│   │   └── energy_forecast_model.pkl
│   │
│   ├── notebooks/                  # Jupyter Notebooks for Logic
│   │   ├── 01_data_generation.ipynb   # Creates Synthetic Data
│   │   ├── 02_data_analysis.ipynb     # EDA & Visualization
│   │   ├── 03_energy_forecasting.ipynb # Model Training
│   │   ├── 04_wastage_detection.ipynb # Anomaly Detection
│   │   └── train_model.py             # Script version of training
│   │
│   └── reports/                    # Generated PDF/MD Reports
│       ├── energy_audit_report.md
│       └── sustainability_report.md
│
├── run_app.bat                     # One-Click Launch Script
└── README.md                       # This Documentation
```

---

## 🤖 AI Algorithms & Logic

### 1. Energy Forecasting Model
*   **Goal**: Predict future energy usage (kWh) based on time and environmental factors.
*   **Algorithm**: **Random Forest Regressor** (Ensemble Learning).
*   **Features Used**:
    *   Building Type (Academic/Hostel/Office)
    *   Area ($m^2$)
    *   Temperature ($^\circ C$)
    *   Humidity (%)
    *   Occupancy Level (Low/Medium/High)
    *   Time Features (Hour, Day of Week, Weekend Flag)
*   **Training Performance**:
    *   **Mean Absolute Error (MAE)**: ~0.30 kWh (Very High Precision)
    *   **Training Size**: 3,700+ Data Points

### 2. Wastage Detection Logic
*   **Logic**: The system compares **Actual Consumption** vs. **AI Predicted Consumption**.
*   **Threshold**: If `Actual usage > 1.2 * Predicted usage` (20% excess), it is flagged as **WASTAGE**.
*   **Output**: Anomalies are logged in `data/wastage_anomalies.csv` and trigger alerts in the dashboard.

### 3. Sustainability Calculator
*   **Carbon Footprint**: Calculated as `Total kWh * 0.85 kg CO2/kWh` (Grid emission factor).
*   **ROI Analysis**: Estimates savings based on optimization recommendations.

---

## 🔮 Generative AI (Gemini Assistant)
*   **Model**: Google Gemini 1.5 Flash.
*   **Role**: Energy Advisor Chatbot.
*   **Integration**: The backend sends the **Current Building Context** (Type, kWh, Temp) along with the user's question to Gemini.
*   **Example Interaction**:
    *   *User*: "Why is consumption high?"
    *   *AI Context*: Building is 'Office', usage 45kWh (High), Temp 18°C.
    *   *AI Reply*: "It looks like the HVAC is cooling aggressively (18°C) despite low occupancy. Try raising the setpoint to 24°C."

---

## ⚙️ How to Run the Project

### Prerequisite
*   **Python 3.10+** installed.
*   **Node.js 16+** installed.

### Option A: One-Click Start (Recommended)
1.  Double-click **`run_app.bat`**.
    *   This script automatically starts the **Backend (Port 8000)** and **Frontend (Port 5173)**.

### Option B: Manual Start

#### 1. Backend
```bash
cd AI_Energy_Optimization/backend
pip install -r requirements.txt
python main.py
# Server runs at http://localhost:8000
```

#### 2. Frontend
```bash
cd AI_Energy_Optimization/frontend
npm install
npm run dev
# App runs at http://localhost:5173
```

---

## 📊 Features
1.  **Real-Time Dashboard**: Grid view of multiple buildings with live KPI updates.
2.  **Interactive Simulation**: "What-If" analysis tool to see how changing temperature/occupancy affects energy.
3.  **Future Crystal Ball**: Pick a future date to predict energy demand using AI.
4.  **Voltix Assistant**: Chat with the AI to get actionable insights.
5.  **Dark/Glass Mode**: Modern, aesthetically pleasing UI with fluid animations.

---
*Developed by Mithun for Advanced Energy Optimization Project.*
