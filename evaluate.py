import os
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from train_xgb_rul_model import generate_training_data

def evaluate_system():
    print("Generating fresh evaluation dataset (30 engines)...")
    # Use different random seed for evaluation
    X, y = generate_training_data(num_engines=30, random_state=42)
    
    print(f"Evaluation data: {X.shape[0]:,} rows, {X.shape[1]} features")

    # 1. Evaluate Primary Model (Accuracy)
    model_path = "xgb_rul_model.json"
    if not os.path.exists(model_path):
        print(f"Error: Primary model not found at {model_path}")
        return

    model = XGBRegressor()
    model.load_model(model_path)
    
    print(f"Assessing model accuracy...")
    preds = model.predict(X)
    
    mae = mean_absolute_error(y, preds)
    rmse = mean_squared_error(y, preds) ** 0.5
    r2 = r2_score(y, preds)

    print("\n" + "="*40)
    print(" HIGH-PERFORMANCE MODEL METRICS")
    print("="*40)
    print(f"MAE:  {mae:,.2f} cycles")
    print(f"RMSE: {rmse:,.2f} cycles")
    print(f"R²:   {r2:.4f}")
    
    if r2 > 0.8:
        print("STATUS: PERFORMANCE MEETS INDUSTRIAL STANDARDS")
    else:
        print("STATUS: PERFORMANCE BELOW TARGET (STILL NEEDS TUNING)")
    print("="*40)

    # 2. Evaluate Quantile Bounds (Reliability)
    lower_path = "xgb_rul_model_lower.json"
    upper_path = "xgb_rul_model_upper.json"
    
    if os.path.exists(lower_path) and os.path.exists(upper_path):
        print("\nAssessing uncertainty model reliability...")
        model_l = XGBRegressor()
        model_l.load_model(lower_path)
        model_u = XGBRegressor()
        model_u.load_model(upper_path)
        
        preds_l = model_l.predict(X)
        preds_u = model_u.predict(X)
        
        # Calculate coverage (how many actual values fall between lower and upper)
        coverage = np.mean((y >= preds_l) & (y <= preds_u))
        print(f"Lower/Upper Coverage: {coverage*100:.1f}%")
        print("Note: Coverage should ideally match the quantile spread (e.g. 0.8 for 0.1-0.9)")
        print("="*40)

if __name__ == "__main__":
    evaluate_system()