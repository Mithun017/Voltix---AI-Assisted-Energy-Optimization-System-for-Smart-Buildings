import joblib
import os
import sys

try:
    # Adjust path assuming this script is run from backend/ directory
    model_path = os.path.join('..', 'models', 'energy_forecast_model.pkl')
    print(f"Loading model from {model_path}...")
    
    if not os.path.exists(model_path):
        print("Model file does not exist!")
        sys.exit(1)
        
    model = joblib.load(model_path)
    print("Model Loaded Successfully.")
    
    if hasattr(model, 'feature_names_in_'):
        print("Expected Features by Model:", list(model.feature_names_in_))
    else:
        print("Model does not have feature_names_in_ attribute.")
        
except Exception as e:
    print(f"Error: {e}")
