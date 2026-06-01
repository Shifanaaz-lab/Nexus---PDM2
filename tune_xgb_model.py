import json
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV, GroupKFold
from train_xgb_rul_model import generate_training_data
import joblib

def tune_hyperparameters():
    print("Generating synthetic training data for tuning (speed-optimized)...")
    # Use only 50 engines for tuning to get results faster
    X, y = generate_training_data(num_engines=50)
    
    groups = X['engine_id'].values

    print(f"Data generated: {X.shape[0]} rows, {X.shape[1]} features")
    
    param_grid = {
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.2],
        'n_estimators': [100, 200, 300],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.7, 0.8, 0.9]
    }
    
    xgb = XGBRegressor(
        objective='reg:squarederror',
        tree_method='hist',
        random_state=42,
        n_jobs=-1
    )
    
    gkf = GroupKFold(n_splits=3)
    
    random_search = RandomizedSearchCV(
        estimator=xgb,
        param_distributions=param_grid,
        n_iter=10, # Fewer iterations for speed
        scoring='neg_root_mean_squared_error',
        cv=gkf,
        verbose=1,
        random_state=42,
        n_jobs=-1
    )
    
    print("Starting Optimized Randomized Search...")
    random_search.fit(X, y, groups=groups)
    
    print("\nBest Parameters found: ")
    print(random_search.best_params_)
    print(f"Best RMSE: {-random_search.best_score_:.4f}")
    
    with open('best_xgb_params.json', 'w') as f:
        json.dump(random_search.best_params_, f, indent=4)
        
    print("Saved best parameters to best_xgb_params.json")

if __name__ == "__main__":
    tune_hyperparameters()

