"""
Comprehensive Model Evaluation and Monitoring System
Production-grade evaluation with real-time monitoring and performance tracking
"""

import os
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
)
from xgboost import XGBRegressor
import joblib

from enhanced_feature_engineering import EnhancedFeatureEngineer
from optimized_model_training import OptimizedModelTrainer


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Structure for evaluation metrics"""
    rmse: float
    mae: float
    r2: float
    mape: float
    residual_std: float
    accuracy_within_10: float
    accuracy_within_20: float
    accuracy_within_50: float
    model_type: str = "XGBoost"
    feature_count: int = 0
    training_time: float = 0.0
    inference_time_ms: float = 0.0


@dataclass
class PerformanceAlert:
    """Structure for performance alerts"""
    timestamp: float
    alert_type: str
    severity: str
    message: str
    metric_value: float
    threshold: float
    engine_id: Optional[int] = None


class ModelEvaluator:
    """
    Comprehensive model evaluation with temporal validation
    and performance degradation detection.
    """
    
    def __init__(self, alert_thresholds: Optional[Dict] = None):
        self.alert_thresholds = alert_thresholds or {
            'rmse_degradation': 0.1,  # 10% increase in RMSE
            'r2_drop': 0.05,          # 5% drop in R²
            'inference_time_ms': 100, # Max inference time
            'prediction_drift': 0.2    # Max prediction drift
        }
        
        self.baseline_metrics: Optional[EvaluationMetrics] = None
        self.performance_history: List[Dict] = []
        self.alerts: List[PerformanceAlert] = []
    
    def evaluate_model_comprehensive(
        self,
        model: XGBRegressor,
        X: pd.DataFrame,
        y: np.ndarray,
        feature_names: List[str],
        temporal_split: bool = True
    ) -> EvaluationMetrics:
        """
        Comprehensive model evaluation with temporal validation.
        """
        start_time = time.time()
        
        if temporal_split:
            # Temporal split to prevent data leakage
            split_idx = int(0.8 * len(X))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
        else:
            # Random split (less realistic for time series)
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Measure inference time
        inference_start = time.time()
        y_pred = model.predict(X_test)
        inference_time = (time.time() - inference_start) * 1000  # Convert to ms
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100
        
        # Residual analysis
        residuals = y_test - y_pred
        residual_std = np.std(residuals)
        
        # Accuracy within thresholds
        accuracy_within_10 = np.mean(np.abs(residuals) <= 10)
        accuracy_within_20 = np.mean(np.abs(residuals) <= 20)
        accuracy_within_50 = np.mean(np.abs(residuals) <= 50)
        
        training_time = time.time() - start_time
        
        metrics = EvaluationMetrics(
            rmse=rmse,
            mae=mae,
            r2=r2,
            mape=mape,
            residual_std=residual_std,
            accuracy_within_10=accuracy_within_10,
            accuracy_within_20=accuracy_within_20,
            accuracy_within_50=accuracy_within_50,
            feature_count=len(feature_names),
            training_time=training_time,
            inference_time_ms=inference_time
        )
        
        # Store baseline if not set
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics
            logger.info("Set baseline metrics")
        
        # Check for performance degradation
        self._check_performance_degradation(metrics)
        
        # Store in history
        self.performance_history.append({
            'timestamp': time.time(),
            'metrics': metrics.__dict__
        })
        
        return metrics
    
    def _check_performance_degradation(self, current_metrics: EvaluationMetrics):
        """Check for performance degradation and create alerts."""
        if self.baseline_metrics is None:
            return
        
        # Check RMSE degradation
        rmse_increase = (current_metrics.rmse - self.baseline_metrics.rmse) / self.baseline_metrics.rmse
        if rmse_increase > self.alert_thresholds['rmse_degradation']:
            alert = PerformanceAlert(
                timestamp=time.time(),
                alert_type="RMSE_DEGRADATION",
                severity="HIGH",
                message=f"RMSE increased by {rmse_increase:.2%}",
                metric_value=current_metrics.rmse,
                threshold=self.baseline_metrics.rmse * (1 + self.alert_thresholds['rmse_degradation'])
            )
            self.alerts.append(alert)
            logger.warning(alert.message)
        
        # Check R² drop
        r2_drop = self.baseline_metrics.r2 - current_metrics.r2
        if r2_drop > self.alert_thresholds['r2_drop']:
            alert = PerformanceAlert(
                timestamp=time.time(),
                alert_type="R2_DROP",
                severity="MEDIUM",
                message=f"R² dropped by {r2_drop:.3f}",
                metric_value=current_metrics.r2,
                threshold=self.baseline_metrics.r2 - self.alert_thresholds['r2_drop']
            )
            self.alerts.append(alert)
            logger.warning(alert.message)
        
        # Check inference time
        if current_metrics.inference_time_ms > self.alert_thresholds['inference_time_ms']:
            alert = PerformanceAlert(
                timestamp=time.time(),
                alert_type="INFERENCE_SLOW",
                severity="MEDIUM",
                message=f"Inference time: {current_metrics.inference_time_ms:.1f}ms",
                metric_value=current_metrics.inference_time_ms,
                threshold=self.alert_thresholds['inference_time_ms']
            )
            self.alerts.append(alert)
            logger.warning(alert.message)
    
    def generate_evaluation_report(self, metrics: EvaluationMetrics) -> str:
        """Generate comprehensive evaluation report."""
        report = f"""
=== MODEL EVALUATION REPORT ===
Model Type: {metrics.model_type}
Feature Count: {metrics.feature_count}
Training Time: {metrics.training_time:.2f}s
Inference Time: {metrics.inference_time_ms:.1f}ms

=== PERFORMANCE METRICS ===
RMSE: {metrics.rmse:.4f}
MAE: {metrics.mae:.4f}
R²: {metrics.r2:.4f}
MAPE: {metrics.mape:.2f}%
Residual Std: {metrics.residual_std:.4f}

=== ACCURACY WITHIN THRESHOLDS ===
±10 cycles: {metrics.accuracy_within_10:.2%}
±20 cycles: {metrics.accuracy_within_20:.2%}
±50 cycles: {metrics.accuracy_within_50:.2%}

=== PERFORMANCE COMPARISON ===
"""
        
        if self.baseline_metrics:
            rmse_change = (metrics.rmse - self.baseline_metrics.rmse) / self.baseline_metrics.rmse
            r2_change = metrics.r2 - self.baseline_metrics.r2
            
            report += f"RMSE Change: {rmse_change:+.2%}\n"
            report += f"R² Change: {r2_change:+.3f}\n"
        
        report += f"\n=== RECENT ALERTS ===\n"
        if self.alerts:
            for alert in self.alerts[-5:]:  # Last 5 alerts
                report += f"{alert.severity}: {alert.message}\n"
        else:
            report += "No recent alerts\n"
        
        return report


class RealTimeMonitor:
    """
    Real-time monitoring of model performance and data drift.
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        drift_threshold: float = 0.1,
        alert_cooldown: float = 300.0  # 5 minutes
    ):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.alert_cooldown = alert_cooldown
        
        # Performance tracking
        self.prediction_buffer: deque = deque(maxlen=window_size)
        self.actual_buffer: deque = deque(maxlen=window_size)
        self.feature_buffer: deque = deque(maxlen=window_size)
        
        # Drift detection
        self.feature_stats: Dict[str, Dict] = {}
        self.prediction_stats: Dict[str, float] = {}
        
        # Alert management
        self.last_alert_time: Dict[str, float] = {}
        self.monitoring_alerts: List[PerformanceAlert] = []
    
    def add_prediction(
        self,
        engine_id: int,
        features: Dict[str, float],
        predicted_rul: float,
        actual_rul: Optional[float] = None
    ):
        """Add prediction to monitoring buffer."""
        self.prediction_buffer.append({
            'engine_id': engine_id,
            'timestamp': time.time(),
            'predicted_rul': predicted_rul,
            'actual_rul': actual_rul,
            'features': features
        })
        
        if actual_rul is not None:
            self.actual_buffer.append(actual_rul)
        
        # Check for data drift
        self._check_data_drift(features)
        
        # Check for prediction drift
        if len(self.prediction_buffer) >= 100:
            self._check_prediction_drift()
    
    def _check_data_drift(self, features: Dict[str, float]):
        """Check for data drift in feature distributions."""
        for feature_name, value in features.items():
            if feature_name not in self.feature_stats:
                self.feature_stats[feature_name] = {
                    'mean': value,
                    'std': 0.0,
                    'count': 1
                }
                continue
            
            stats = self.feature_stats[feature_name]
            
            # Update running statistics
            stats['count'] += 1
            delta = value - stats['mean']
            stats['mean'] += delta / stats['count']
            stats['std'] += delta * (value - stats['mean'])
            
            # Check for drift (simplified)
            if stats['count'] > 100:
                current_std = np.sqrt(stats['std'] / stats['count'])
                z_score = abs(value - stats['mean']) / (current_std + 1e-8)
                
                if z_score > 3.0:  # 3-sigma rule
                    self._create_monitoring_alert(
                        "DATA_DRIFT",
                        f"Feature {feature_name} drift detected (z-score: {z_score:.2f})",
                        z_score,
                        3.0,
                        feature_name
                    )
    
    def _check_prediction_drift(self):
        """Check for prediction drift."""
        if len(self.prediction_buffer) < 100:
            return
        
        recent_predictions = [p['predicted_rul'] for p in list(self.prediction_buffer)[-100:]]
        current_mean = np.mean(recent_predictions)
        current_std = np.std(recent_predictions)
        
        if 'prediction_mean' not in self.prediction_stats:
            self.prediction_stats['prediction_mean'] = current_mean
            self.prediction_stats['prediction_std'] = current_std
            return
        
        # Check for drift in prediction distribution
        baseline_mean = self.prediction_stats['prediction_mean']
        mean_drift = abs(current_mean - baseline_mean) / (abs(baseline_mean) + 1e-8)
        
        if mean_drift > self.drift_threshold:
            self._create_monitoring_alert(
                "PREDICTION_DRIFT",
                f"Prediction mean drift: {mean_drift:.2%}",
                mean_drift,
                self.drift_threshold
            )
    
    def _create_monitoring_alert(
        self,
        alert_type: str,
        message: str,
        metric_value: float,
        threshold: float,
        engine_id: Optional[int] = None
    ):
        """Create monitoring alert with cooldown."""
        current_time = time.time()
        
        # Check cooldown
        if (alert_type in self.last_alert_time and 
            current_time - self.last_alert_time[alert_type] < self.alert_cooldown):
            return
        
        alert = PerformanceAlert(
            timestamp=current_time,
            alert_type=alert_type,
            severity="MEDIUM",
            message=message,
            metric_value=metric_value,
            threshold=threshold,
            engine_id=engine_id
        )
        
        self.monitoring_alerts.append(alert)
        self.last_alert_time[alert_type] = current_time
        
        logger.warning(f"MONITORING ALERT: {message}")
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring metrics."""
        if not self.prediction_buffer:
            return {"status": "No data"}
        
        recent_predictions = [p['predicted_rul'] for p in list(self.prediction_buffer)[-100:]]
        
        summary = {
            "total_predictions": len(self.prediction_buffer),
            "recent_predictions": len(recent_predictions),
            "avg_predicted_rul": np.mean(recent_predictions),
            "std_predicted_rul": np.std(recent_predictions),
            "total_alerts": len(self.monitoring_alerts),
            "recent_alerts": len([a for a in self.monitoring_alerts 
                                if time.time() - a.timestamp < 3600])  # Last hour
        }
        
        if self.actual_buffer:
            recent_actuals = list(self.actual_buffer)[-len(recent_predictions):]
            if len(recent_actuals) == len(recent_predictions):
                residuals = np.array(recent_actuals) - np.array(recent_predictions)
                summary.update({
                    "recent_rmse": np.sqrt(np.mean(residuals**2)),
                    "recent_mae": np.mean(np.abs(residuals)),
                    "recent_r2": r2_score(recent_actuals, recent_predictions)
                })
        
        return summary


class PerformanceVisualizer:
    """
    Visualization tools for model performance and monitoring.
    """
    
    def __init__(self, output_dir: str = "performance_plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def plot_prediction_vs_actual(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        title: str = "Predictions vs Actual",
        save_path: Optional[str] = None
    ):
        """Plot predictions vs actual values."""
        plt.figure(figsize=(10, 6))
        
        # Scatter plot
        plt.scatter(y_true, y_pred, alpha=0.6, s=20)
        
        # Perfect prediction line
        min_val, max_val = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
        
        plt.xlabel('Actual RUL')
        plt.ylabel('Predicted RUL')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add metrics
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        plt.text(0.05, 0.95, f'R² = {r2:.3f}\nRMSE = {rmse:.3f}', 
                transform=plt.gca().transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(f"{self.output_dir}/predictions_vs_actual.png", dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def plot_residuals(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        title: str = "Residual Analysis",
        save_path: Optional[str] = None
    ):
        """Plot residual analysis."""
        residuals = y_true - y_pred
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Residuals vs Predicted
        axes[0, 0].scatter(y_pred, residuals, alpha=0.6, s=20)
        axes[0, 0].axhline(y=0, color='r', linestyle='--')
        axes[0, 0].set_xlabel('Predicted RUL')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].set_title('Residuals vs Predicted')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Histogram of residuals
        axes[0, 1].hist(residuals, bins=50, alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Residuals')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Distribution of Residuals')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Residuals vs Actual
        axes[1, 1].scatter(y_true, residuals, alpha=0.6, s=20)
        axes[1, 1].axhline(y=0, color='r', linestyle='--')
        axes[1, 1].set_xlabel('Actual RUL')
        axes[1, 1].set_ylabel('Residuals')
        axes[1, 1].set_title('Residuals vs Actual')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(f"{self.output_dir}/residual_analysis.png", dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def plot_feature_importance(
        self,
        model: XGBRegressor,
        feature_names: List[str],
        top_n: int = 20,
        title: str = "Feature Importance",
        save_path: Optional[str] = None
    ):
        """Plot feature importance."""
        # Get feature importance
        importance = model.feature_importances_
        
        # Create DataFrame and sort
        feature_importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Take top N features
        top_features = feature_importance_df.head(top_n)
        
        plt.figure(figsize=(12, 8))
        sns.barplot(data=top_features, x='importance', y='feature')
        plt.title(f'{title} (Top {top_n})')
        plt.xlabel('Importance')
        plt.ylabel('Features')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(f"{self.output_dir}/feature_importance.png", dpi=300, bbox_inches='tight')
        
        plt.close()
        
        return feature_importance_df


def main():
    """
    Example usage of evaluation and monitoring system.
    """
    # Load trained model and feature engineer
    try:
        model = XGBRegressor()
        model.load_model("optimized_xgb_rul_model.json")
        
        with open("optimized_xgb_rul_model_metadata.json", 'r') as f:
            metadata = json.load(f)
        
        feature_engineer = joblib.load("optimized_xgb_rul_model_feature_engineer.pkl")
        
        # Generate test data
        trainer = OptimizedModelTrainer()
        X_test, y_test = trainer.generate_training_data(num_engines=20)
        
        # Initialize evaluator
        evaluator = ModelEvaluator()
        
        # Evaluate model
        metrics = evaluator.evaluate_model_comprehensive(
            model, X_test, y_test, metadata['feature_names']
        )
        
        # Generate report
        report = evaluator.generate_evaluation_report(metrics)
        print(report)
        
        # Initialize visualizer
        visualizer = PerformanceVisualizer()
        
        # Make predictions for visualization
        y_pred = model.predict(X_test)
        
        # Create plots
        visualizer.plot_prediction_vs_actual(y_test, y_pred)
        visualizer.plot_residuals(y_test, y_pred)
        feature_importance = visualizer.plot_feature_importance(
            model, metadata['feature_names']
        )
        
        # Initialize real-time monitor
        monitor = RealTimeMonitor()
        
        # Simulate real-time predictions
        for i in range(min(100, len(X_test))):
            features = X_test.iloc[i].to_dict()
            predicted_rul = y_pred[i]
            actual_rul = y_test[i]
            
            monitor.add_prediction(
                engine_id=int(features.get('engine_id', 0)),
                features=features,
                predicted_rul=predicted_rul,
                actual_rul=actual_rul
            )
        
        # Get monitoring summary
        summary = monitor.get_monitoring_summary()
        print(f"\n=== MONITORING SUMMARY ===")
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        return evaluator, monitor, visualizer
        
    except Exception as e:
        logger.error(f"Error in evaluation: {e}")
        return None, None, None


if __name__ == "__main__":
    evaluator, monitor, visualizer = main()
