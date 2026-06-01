"""
Cross-Engine Model Trainer for Time-Series Telemetry
Optimized for generalization across different engine patterns
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Set
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import optuna

from time_series_optimized_features import TimeSeriesOptimizedFeatureEngineer
from real_time_engine_telemetry import EngineState, ROLLING_WINDOW, MAX_RUL_CAP


class CrossEngineModelTrainer:
    """
    Model trainer optimized for cross-engine generalization
    Uses engine-aware validation and feature selection
    """
    
    def __init__(
        self,
        n_trials: int = 100,
        cv_folds: int = 5,
        random_state: int = 42,
        use_optuna: bool = True,
        engine_aware_validation: bool = True
    ):
        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.use_optuna = use_optuna
        self.engine_aware_validation = engine_aware_validation
        
        self.best_params = None
        self.feature_engineer = None
        self.engine_clusters = {}
        self.feature_importance = {}
        self.engine_performance = {}
        
        # Cross-engine optimized parameters
        self.default_params = {
            'n_estimators': 300,
            'max_depth': 6,
            'learning_rate': 0.03,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'colsample_bylevel': 0.8,
            'reg_alpha': 0.2,  # Higher L1 for cross-engine generalization
            'reg_lambda': 1.5,  # Higher L2 for cross-engine generalization
            'min_child_weight': 3,  # Higher to prevent overfitting
            'gamma': 0.2,  # Higher for more conservative splits
            'tree_method': 'hist',
            'grow_policy': 'depthwise',
            'max_leaves': 0,
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'n_jobs': -1,
            'random_state': random_state
        }
    
    def _create_engine_aware_split(
        self, 
        X: pd.DataFrame, 
        y: np.ndarray
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Create engine-aware cross-validation splits
        Ensures no engine appears in both train and validation sets
        """
        # Group by engine_id
        engine_groups = X.groupby('engine_id')
        engine_ids = list(engine_groups.groups.keys())
        np.random.shuffle(engine_ids)
        
        splits = []
        fold_size = len(engine_ids) // self.cv_folds
        
        for fold in range(self.cv_folds):
            start_idx = fold * fold_size
            end_idx = start_idx + fold_size if fold < self.cv_folds - 1 else len(engine_ids)
            
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
    
    def _cluster_engines(
        self, 
        X: pd.DataFrame, 
        n_clusters: int = 3
    ) -> Dict[int, int]:
        """
        Cluster engines based on their operational patterns
        Helps identify different engine types for better generalization
        """
        # Extract engine-level features
        engine_features = []
        engine_ids = []
        
        for engine_id, group in X.groupby('engine_id'):
            # Compute engine-level statistics
            features = {
                'mean_cycle': group['cycle'].mean(),
                'std_cycle': group['cycle'].std(),
                'mean_s1': group['s1'].mean(),
                'std_s1': group['s1'].std(),
                'mean_s2': group['s2'].mean(),
                'std_s2': group['s2'].std(),
                'mean_s3': group['s3'].mean(),
                'std_s3': group['s3'].std(),
                'cycle_range': group['cycle'].max() - group['cycle'].min(),
                'data_points': len(group)
            }
            
            engine_features.append(list(features.values()))
            engine_ids.append(engine_id)
        
        # Cluster engines
        if len(engine_features) >= n_clusters:
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state)
            clusters = kmeans.fit_predict(engine_features)
            
            self.engine_clusters = dict(zip(engine_ids, clusters))
            
            print(f"Clustered {len(engine_ids)} engines into {n_clusters} clusters")
            for cluster_id in range(n_clusters):
                engines_in_cluster = [eid for eid, cid in self.engine_clusters.items() if cid == cluster_id]
                print(f"  Cluster {cluster_id}: {len(engines_in_cluster)} engines")
        
        return self.engine_clusters
    
    def _evaluate_cross_engine_performance(
        self,
        model: XGBRegressor,
        X: pd.DataFrame,
        y: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluate model performance across different engines
        """
        if self.engine_aware_validation:
            splits = self._create_engine_aware_split(X, y)
        else:
            # Standard cross-validation
            from sklearn.model_selection import KFold
            kf = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
            splits = list(kf.split(X))
        
        all_predictions = []
        all_actuals = []
        engine_predictions = {}
        
        for train_idx, val_idx in splits:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Train model
            temp_model = XGBRegressor(**model.get_params())
            temp_model.fit(X_train, y_train, verbose=False)
            
            # Predict on validation
            y_pred = temp_model.predict(X_val)
            
            all_predictions.extend(y_pred)
            all_actuals.extend(y_val)
            
            # Track performance per engine
            val_engines = X_val['engine_id'].unique()
            for engine_id in val_engines:
                engine_mask = X_val['engine_id'] == engine_id
                engine_pred = y_pred[engine_mask]
                engine_actual = y_val[engine_mask]
                
                if engine_id not in engine_predictions:
                    engine_predictions[engine_id] = []
                engine_predictions[engine_id].extend(zip(engine_actual, engine_pred))
        
        # Calculate overall metrics
        all_predictions = np.array(all_predictions)
        all_actuals = np.array(all_actuals)
        
        overall_metrics = {
            'rmse': np.sqrt(mean_squared_error(all_actuals, all_predictions)),
            'mae': mean_absolute_error(all_actuals, all_predictions),
            'r2': r2_score(all_actuals, all_predictions),
            'mape': np.mean(np.abs((all_actuals - all_predictions) / (all_actuals + 1e-8))) * 100
        }
        
        # Calculate per-engine metrics
        per_engine_metrics = {}
        for engine_id, predictions in engine_predictions.items():
            if len(predictions) > 0:
                actuals, preds = zip(*predictions)
                actuals, preds = np.array(actuals), np.array(preds)
                
                per_engine_metrics[engine_id] = {
                    'rmse': np.sqrt(mean_squared_error(actuals, preds)),
                    'mae': mean_absolute_error(actuals, preds),
                    'r2': r2_score(actuals, preds),
                    'samples': len(predictions)
                }
        
        self.engine_performance = per_engine_metrics
        
        # Calculate cross-engine stability
        engine_r2_scores = [metrics['r2'] for metrics in per_engine_metrics.values()]
        cross_engine_stability = np.std(engine_r2_scores)
        
        overall_metrics['cross_engine_stability'] = cross_engine_stability
        overall_metrics['worst_engine_r2'] = min(engine_r2_scores) if engine_r2_scores else 0
        overall_metrics['best_engine_r2'] = max(engine_r2_scores) if engine_r2_scores else 0
        
        return overall_metrics
    
    def _objective_function(
        self, 
        trial: optuna.Trial, 
        X: pd.DataFrame, 
        y: np.ndarray
    ) -> float:
        """
        Optuna objective function for cross-engine optimization
        """
        # Define hyperparameter search space (more conservative for cross-engine)
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 200, 800),
            'max_depth': trial.suggest_int('max_depth', 3, 8),  # Shallower trees
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.05, log=True),
            'subsample': trial.suggest_float('subsample', 0.7, 0.9),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 0.9),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.7, 0.9),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.1, 0.5),  # Higher regularization
            'reg_lambda': trial.suggest_float('reg_lambda', 1.0, 3.0),  # Higher regularization
            'min_child_weight': trial.suggest_int('min_child_weight', 2, 6),  # Higher values
            'gamma': trial.suggest_float('gamma', 0.1, 0.5),  # Higher gamma
        }
        
        # Fixed parameters
        params.update({
            'tree_method': 'hist',
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'n_jobs': -1,
            'random_state': self.random_state
        })
        
        # Cross-validation with engine awareness
        if self.engine_aware_validation:
            splits = self._create_engine_aware_split(X, y)
        else:
            from sklearn.model_selection import KFold
            kf = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
            splits = list(kf.split(X))
        
        cv_scores = []
        engine_stability_scores = []
        
        for train_idx, val_idx in splits:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Train model
            model = XGBRegressor(**params)
            model.fit(X_train, y_train, verbose=False)
            
            # Evaluate
            y_pred = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            cv_scores.append(rmse)
            
            # Calculate per-engine stability
            val_engines = X_val['engine_id'].unique()
            if len(val_engines) > 1:
                engine_r2_scores = []
                for engine_id in val_engines:
                    engine_mask = X_val['engine_id'] == engine_id
                    if engine_mask.sum() > 1:
                        engine_actual = y_val[engine_mask]
                        engine_pred = y_pred[engine_mask]
                        engine_r2 = r2_score(engine_actual, engine_pred)
                        engine_r2_scores.append(engine_r2)
                
                if engine_r2_scores:
                    stability = 1.0 - np.std(engine_r2_scores)  # Higher is better
                    engine_stability_scores.append(stability)
        
        # Primary objective: RMSE
        mean_rmse = np.mean(cv_scores)
        
        # Secondary objective: Cross-engine stability
        if engine_stability_scores:
            mean_stability = np.mean(engine_stability_scores)
            # Combine objectives (weighted sum)
            combined_score = mean_rmse - 0.1 * mean_stability  # Penalty for instability
        else:
            combined_score = mean_rmse
        
        return combined_score
    
    def optimize_hyperparameters(
        self, 
        X: pd.DataFrame, 
        y: np.ndarray
    ) -> Dict:
        """
        Optimize hyperparameters with cross-engine awareness
        """
        if not self.use_optuna:
            print("Using default cross-engine optimized parameters...")
            return self.default_params.copy()
        
        print(f"Starting cross-engine hyperparameter optimization with {self.n_trials} trials...")
        
        # Cluster engines for better understanding
        self._cluster_engines(X)
        
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
        
        print(f"Best cross-engine RMSE: {study.best_value:.4f}")
        print(f"Best parameters: {self.best_params}")
        
        return self.best_params
    
    def train_cross_engine_model(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        params: Optional[Dict] = None
    ) -> XGBRegressor:
        """
        Train model with cross-engine generalization focus
        """
        if params is None:
            params = self.best_params if self.best_params else self.default_params
        
        # Create engine-aware train/validation split
        if self.engine_aware_validation:
            splits = self._create_engine_aware_split(X, y)
            train_idx, val_idx = splits[0]  # Use first split for final training
        else:
            from sklearn.model_selection import train_test_split
            train_idx, val_idx = train_test_split(
                np.arange(len(X)), test_size=0.2, random_state=self.random_state
            )
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        print(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        print(f"Training engines: {len(X_train['engine_id'].unique())}")
        print(f"Validation engines: {len(X_val['engine_id'].unique())}")
        
        # Train model
        model = XGBRegressor(**params)
        model.fit(X_train, y_train, verbose=False)
        
        # Evaluate cross-engine performance
        metrics = self._evaluate_cross_engine_performance(model, X, y)
        
        print(f"Cross-Engine Performance:")
        print(f"  Overall RMSE: {metrics['rmse']:.4f}")
        print(f"  Overall R²: {metrics['r2']:.4f}")
        print(f"  Cross-Engine Stability: {metrics['cross_engine_stability']:.4f}")
        print(f"  Worst Engine R²: {metrics['worst_engine_r2']:.4f}")
        print(f"  Best Engine R²: {metrics['best_engine_r2']:.4f}")
        
        return model
    
    def generate_cross_engine_training_data(
        self,
        num_engines: int = 100,
        rul_horizon_multiplier: float = 1.5
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate training data with diverse engine patterns
        """
        print(f"Generating diverse training data for {num_engines} engines...")
        
        rng = np.random.default_rng(self.random_state)
        self.feature_engineer = TimeSeriesOptimizedFeatureEngineer(
            rolling_window=15,
            use_scaler=True,
            scaler_type="robust"
        )
        
        rows = []
        labels = []
        
        for engine_id in range(1, num_engines + 1):
            # Create diverse engine patterns
            eng = EngineState(engine_id=engine_id)
            eng.initialize_random(rng)
            
            # Warm-up history
            for _ in range(ROLLING_WINDOW):
                _, sensors, op_settings = eng.next_reading(rng)
            
            max_cycles = int(eng.design_life * rul_horizon_multiplier)
            
            for _ in range(max_cycles):
                cycle, sensors, op_settings = eng.next_reading(rng)
                
                # Build temporal features
                engine_state = {
                    'engine_id': eng.engine_id,
                    'design_life': eng.design_life,
                    'history': np.array(eng.history)
                }
                
                feat = self.feature_engineer.build_temporal_feature_row(
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
        
        # Fit feature engineer
        self.feature_engineer.fit(rows)
        
        # Transform features
        X_transformed = pd.DataFrame(self.feature_engineer.transform(rows))
        
        print(f"Generated {X_transformed.shape[0]:,} samples with {X_transformed.shape[1]} features")
        print(f"Engines: {X_transformed['engine_id'].nunique()}")
        
        return X_transformed, y
    
    def optimize_and_prune_features(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        model: XGBRegressor
    ) -> Tuple[pd.DataFrame, Set[str]]:
        """
        Optimize feature set using importance and redundancy analysis
        """
        print("Optimizing feature set...")
        
        # Get feature importance
        feature_names = list(X.columns)
        importance_dict = dict(zip(feature_names, model.feature_importances_))
        
        # Prune by importance
        features_to_remove_importance = self.feature_engineer.prune_features_by_importance(
            importance_dict, 
            importance_threshold=0.001
        )
        
        print(f"Removed {len(features_to_remove_importance)} features by importance")
        
        # Remove redundant features
        if len(features_to_remove_importance) < len(feature_names) - 10:  # Keep some features
            remaining_features = [f for f in feature_names if f not in features_to_remove_importance]
            X_remaining = X[remaining_features]
            
            features_to_remove_redundancy, mi_scores = self.feature_engineer.remove_redundant_features(
                X_remaining, y
            )
            
            print(f"Removed {len(features_to_remove_redundancy)} redundant features")
            
            all_removed = features_to_remove_importance.union(features_to_remove_redundancy)
        else:
            all_removed = features_to_remove_importance
        
        # Keep only valid features
        valid_features = self.feature_engineer.get_optimized_feature_names()
        final_features = [f for f in valid_features if f in X.columns]
        
        X_optimized = X[final_features]
        
        print(f"Final feature set: {len(final_features)} features")
        
        # Get feature statistics
        stats = self.feature_engineer.get_feature_statistics()
        print(f"Feature optimization statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        return X_optimized, all_removed
    
    def save_cross_engine_model(
        self,
        model: XGBRegressor,
        output_prefix: str = "cross_engine_optimized_model"
    ):
        """
        Save cross-engine optimized model and metadata
        """
        # Save main model
        model.save_model(f"{output_prefix}.json")
        
        # Save feature engineer
        import joblib
        joblib.dump(self.feature_engineer, f"{output_prefix}_feature_engineer.pkl")
        
        # Save metadata
        metadata = {
            'best_params': self.best_params,
            'feature_names': self.feature_engineer.get_optimized_feature_names(),
            'engine_clusters': self.engine_clusters,
            'engine_performance': self.engine_performance,
            'feature_importance': self.feature_engineer.feature_importance,
            'model_type': 'CrossEngineOptimized',
            'feature_engineering': 'TimeSeriesOptimized',
            'validation_type': 'engine_aware' if self.engine_aware_validation else 'standard',
            'feature_statistics': self.feature_engineer.get_feature_statistics()
        }
        
        with open(f"{output_prefix}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved cross-engine optimized model to {output_prefix}*")


def main():
    """
    Main training pipeline for cross-engine optimization
    """
    trainer = CrossEngineModelTrainer(
        n_trials=30,  # Reduced for faster execution
        cv_folds=5,
        use_optuna=True,
        engine_aware_validation=True
    )
    
    # Generate diverse training data
    X, y = trainer.generate_cross_engine_training_data(num_engines=50)
    
    # Optimize hyperparameters
    best_params = trainer.optimize_hyperparameters(X, y)
    
    # Train cross-engine model
    model = trainer.train_cross_engine_model(X, y, best_params)
    
    # Optimize features
    X_optimized, removed_features = trainer.optimize_and_prune_features(X, y, model)
    
    # Retrain on optimized features
    print("\nRetraining on optimized feature set...")
    optimized_model = trainer.train_cross_engine_model(X_optimized, y, best_params)
    
    # Save model
    trainer.save_cross_engine_model(optimized_model, "cross_engine_optimized_model")
    
    return trainer, optimized_model


if __name__ == "__main__":
    trainer, model = main()
