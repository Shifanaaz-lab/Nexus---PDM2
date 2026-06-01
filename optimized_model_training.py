"""
Optimized XGBoost Model Training for Predictive Maintenance
Production-ready training pipeline with hyperparameter optimization and proper validation
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xgboost as xgb
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import optuna

from enhanced_feature_engineering import EnhancedFeatureEngineer
from real_time_engine_telemetry import EngineState, ROLLING_WINDOW, MAX_RUL_CAP


class OptimizedModelTrainer:
    """
    Production-grade model trainer with:
    - Advanced hyperparameter optimization
    - Proper time-series cross-validation
    - Early stopping and overfitting prevention
    - Model ensemble capabilities
    - Performance monitoring
    """
    
    def __init__(
        self,
        n_trials: int = 100,
        cv_folds: int = 5,
        random_state: int = 42,
        use_optuna: bool = True
    ):
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.use_optuna = use_optuna
        
        self.best_params = None
        self.feature_engineer = None
        self.training_history = []
        
        # Default optimized parameters (based on research for RUL prediction)
        self.default_params = {
            'n_estimators': 500,
            'max_depth': 8,
            'learning_rate': 0.01,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'colsample_bylevel': 0.8,
            'reg_alpha': 0.1,  # L1 regularization
            'reg_lambda': 1.0,  # L2 regularization
            'min_child_weight': 1,
            'gamma': 0.1,
            'tree_method': 'hist',
            'grow_policy': 'depthwise',
            'max_leaves': 0,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'n_jobs': -1,
            'random_state': random_state
        }
    
    def _create_time_series_split(self, X: pd.DataFrame, y: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Create time-series aware splits that prevent data leakage between engines.
        """
        # Group by engine_id to maintain temporal order within each engine
        engine_groups = X.groupby('engine_id')
        splits = []
        
        # Create splits based on engine groups
        engine_ids = list(engine_groups.groups.keys())
        n_engines = len(engine_ids)
        
        for fold in range(self.cv_folds):
            # Use engines for validation that haven't been seen in training
            val_size = max(1, n_engines // self.cv_folds)
            start_idx = fold * val_size
            end_idx = min((fold + 1) * val_size, n_engines)
            
            val_engine_ids = engine_ids[start_idx:end_idx]
            train_engine_ids = [eid for eid in engine_ids if eid not in val_engine_ids]
            
            # Get indices for training and validation
            train_indices = []
            val_indices = []
            
            for engine_id in train_engine_ids:
                train_indices.extend(engine_groups.groups[engine_id])
            
            for engine_id in val_engine_ids:
                val_indices.extend(engine_groups.groups[engine_id])
            
            splits.append((np.array(train_indices), np.array(val_indices)))
        
        return splits
    
    def _objective_function(self, trial, X: pd.DataFrame, y: np.ndarray) -> float:
        """
        Optuna objective function for hyperparameter optimization.
        """
        # Define hyperparameter search space
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 1000),
            'max_depth': trial.suggest_int('max_depth', 4, 12),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.1, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.6, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0.0, 1.0),
            'max_leaves': trial.suggest_int('max_leaves', 0, 255),
        }
        
        # Fixed parameters
        params.update({
            'tree_method': 'hist',
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'n_jobs': -1,
            'random_state': self.random_state
        })
        
        # Time series cross-validation
        splits = self._create_time_series_split(X, y)
        cv_scores = []
        
        for train_idx, val_idx in splits:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Train model with early stopping
            model = XGBRegressor(**params)
            
            eval_set = [(X_val, y_val)]
            model.fit(
                X_train, y_train,
                eval_set=eval_set,
                early_stopping_rounds=50,
                verbose=False
            )
            
            # Evaluate on validation set
            y_pred = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            cv_scores.append(rmse)
        
        return np.mean(cv_scores)
    
    def optimize_hyperparameters(
        self, 
        X: pd.DataFrame, 
        y: np.ndarray
    ) -> Dict:
        """
        Optimize hyperparameters using Optuna.
        """
        if not self.use_optuna:
            print("Using default optimized parameters...")
            return self.default_params.copy()
        
        print(f"Starting hyperparameter optimization with {self.n_trials} trials...")
        
        study = optuna.create_study(
            direction='minimize',
            sampler=optuna.samplers.TPESampler(seed=self.random_state)
        )
        
        study.optimize(
            lambda trial: self._objective_function(trial, X, y),
            n_trials=self.n_trials,
            show_progress_bar=True
        )
        
        self.best_params = study.best_params
        self.best_params.update({
            'tree_method': 'hist',
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'n_jobs': -1,
            'random_state': self.random_state
        })
        
        print(f"Best RMSE: {study.best_value:.4f}")
        print(f"Best parameters: {self.best_params}")
        
        return self.best_params
    
    def train_model_with_early_stopping(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        params: Optional[Dict] = None,
        validation_split: float = 0.2
    ) -> XGBRegressor:
        """
        Train model with proper early stopping and validation.
        """
        if params is None:
            params = self.best_params if self.best_params else self.default_params
        
        # Create time-aware validation split
        splits = self._create_time_series_split(X, y)
        train_idx, val_idx = splits[0]  # Use first split for final training
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        
        # Train model with early stopping
        model = XGBRegressor(**params)
        
        eval_set = [(X_val, y_val)]
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            early_stopping_rounds=100,
            verbose=False
        )
        
        # Store training history
        self.training_history.append({
            'params': params,
            'best_iteration': model.best_iteration,
            'best_score': model.best_score
        })
        
        return model
    
    def evaluate_model(
        self,
        model: XGBRegressor,
        X: pd.DataFrame,
        y: np.ndarray
    ) -> Dict[str, float]:
        """
        Comprehensive model evaluation.
        """
        # Time series cross-validation evaluation
        splits = self._create_time_series_split(X, y)
        predictions = []
        actuals = []
        
        for train_idx, val_idx in splits:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Train model on training split
            temp_model = XGBRegressor(**model.get_params())
            temp_model.fit(X_train, y_train, verbose=False)
            
            # Predict on validation split
            y_pred = temp_model.predict(X_val)
            predictions.extend(y_pred)
            actuals.extend(y_val)
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Calculate metrics
        metrics = {
            'rmse': np.sqrt(mean_squared_error(actuals, predictions)),
            'mae': mean_absolute_error(actuals, predictions),
            'r2': r2_score(actuals, predictions),
            'mape': np.mean(np.abs((actuals - predictions) / (actuals + 1e-8))) * 100
        }
        
        # Additional metrics for RUL prediction
        residual_std = np.std(actuals - predictions)
        metrics['residual_std'] = residual_std
        
        # Accuracy within different thresholds
        for threshold in [10, 20, 50]:
            accuracy = np.mean(np.abs(actuals - predictions) <= threshold)
            metrics[f'accuracy_within_{threshold}'] = accuracy
        
        return metrics
    
    def train_ensemble_models(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        n_models: int = 3
    ) -> List[XGBRegressor]:
        """
        Train ensemble of models for robustness.
        """
        models = []
        
        for i in range(n_models):
            print(f"Training ensemble model {i+1}/{n_models}...")
            
            # Vary parameters slightly for diversity
            params = self.best_params.copy() if self.best_params else self.default_params.copy()
            
            # Add some randomness to prevent overfitting
            params['random_state'] = self.random_state + i
            params['subsample'] = max(0.6, params['subsample'] - i * 0.05)
            params['colsample_bytree'] = max(0.6, params['colsample_bytree'] - i * 0.05)
            
            model = self.train_model_with_early_stopping(X, y, params)
            models.append(model)
        
        return models
    
    def generate_training_data(
        self,
        num_engines: int = 100,
        rul_horizon_multiplier: float = 1.5
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate enhanced training data with proper feature engineering.
        """
        print(f"Generating training data for {num_engines} engines...")
        
        rng = np.random.default_rng(self.random_state)
        self.feature_engineer = EnhancedFeatureEngineer(rolling_window=30)
        
        rows = []
        labels = []
        
        for engine_id in range(1, num_engines + 1):
            eng = EngineState(engine_id=engine_id)
            eng.initialize_random(rng)
            
            # Warm-up history
            for _ in range(ROLLING_WINDOW):
                _, sensors, op_settings = eng.next_reading(rng)
            
            max_cycles = int(eng.design_life * rul_horizon_multiplier)
            
            for _ in range(max_cycles):
                cycle, sensors, op_settings = eng.next_reading(rng)
                
                # Build enhanced features
                engine_state = {
                    'engine_id': eng.engine_id,
                    'design_life': eng.design_life,
                    'history': np.array(eng.history)
                }
                
                feat = self.feature_engineer.build_feature_row(
                    engine_state, cycle, sensors, op_settings
                )
                
                # Piecewise RUL labeling
                raw_rul = eng.design_life - cycle
                rul = min(float(raw_rul), float(MAX_RUL_CAP))
                rul = max(rul, 0.0)
                
                rows.append(feat)
                labels.append(rul)
        
        X = pd.DataFrame(rows)
        y = np.array(labels, dtype=float)
        
        # Fit feature engineer on training data
        self.feature_engineer.fit(rows)
        
        # Transform features
        X_transformed = pd.DataFrame(self.feature_engineer.transform(rows))
        
        print(f"Generated {X_transformed.shape[0]:,} samples with {X_transformed.shape[1]} features")
        
        return X_transformed, y
    
    def save_models(
        self,
        models: List[XGBRegressor],
        output_prefix: str = "optimized_xgb_rul_model"
    ):
        """
        Save trained models and metadata.
        """
        # Save main model
        models[0].save_model(f"{output_prefix}.json")
        
        # Save ensemble models
        for i, model in enumerate(models[1:], 1):
            model.save_model(f"{output_prefix}_ensemble_{i}.json")
        
        # Save feature engineer
        import joblib
        joblib.dump(self.feature_engineer, f"{output_prefix}_feature_engineer.pkl")
        
        # Save metadata
        metadata = {
            'best_params': self.best_params,
            'feature_names': self.feature_engineer.get_feature_names(),
            'training_history': self.training_history,
            'model_type': 'XGBRegressor',
            'feature_engineering': 'EnhancedFeatureEngineer'
        }
        
        with open(f"{output_prefix}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved models and metadata to {output_prefix}*")


def main():
    """
    Main training pipeline.
    """
    trainer = OptimizedModelTrainer(
        n_trials=50,  # Reduced for faster execution
        cv_folds=5,
        use_optuna=True
    )
    
    # Generate training data
    X, y = trainer.generate_training_data(num_engines=50)
    
    # Optimize hyperparameters
    best_params = trainer.optimize_hyperparameters(X, y)
    
    # Train ensemble models
    models = trainer.train_ensemble_models(X, y, n_models=3)
    
    # Evaluate main model
    metrics = trainer.evaluate_model(models[0], X, y)
    
    print("\n=== Model Performance ===")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")
    
    # Save models
    trainer.save_models(models, "optimized_xgb_rul_model")
    
    return trainer, models, metrics


if __name__ == "__main__":
    trainer, models, metrics = main()
