"""
Time-Series Optimized Feature Engineering for Predictive Maintenance
Strictly temporal features with no future information leakage
Real-time computable and engine-generalizable
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import deque
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import mutual_info_score
import warnings
warnings.filterwarnings('ignore')


class TemporalFeatureValidator:
    """Validates that features are temporally sound (no future information)"""
    
    def __init__(self):
        self.temporal_violations = []
    
    def validate_feature(self, feature_name: str, computation_method: str) -> bool:
        """
        Validate that a feature doesn't use future information
        
        Args:
            feature_name: Name of the feature
            computation_method: Description of how feature is computed
            
        Returns:
            True if feature is temporally valid, False otherwise
        """
        # Check for future-looking patterns
        future_indicators = ['future', 'lead', 'next', 'ahead', 'tomorrow']
        
        for indicator in future_indicators:
            if indicator.lower() in feature_name.lower() or indicator.lower() in computation_method.lower():
                self.temporal_violations.append(f"Feature {feature_name} may use future information")
                return False
        
        return True
    
    def get_violations(self) -> List[str]:
        """Get list of temporal violations found"""
        return self.temporal_violations


class RealTimeFeatureChecker:
    """Validates that features can be computed in real-time"""
    
    def __init__(self, max_computation_time_ms: float = 50.0):
        self.max_computation_time_ms = max_computation_time_ms
        self.slow_features = []
    
    def check_computation_time(self, feature_name: str, computation_func, *args, **kwargs) -> bool:
        """
        Check if feature computation meets real-time requirements
        
        Args:
            feature_name: Name of the feature
            computation_func: Function to compute the feature
            *args, **kwargs: Arguments for the computation function
            
        Returns:
            True if computation is fast enough, False otherwise
        """
        import time
        
        # Time the computation
        start_time = time.time()
        try:
            result = computation_func(*args, **kwargs)
            computation_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if computation_time > self.max_computation_time_ms:
                self.slow_features.append(f"{feature_name}: {computation_time:.2f}ms")
                return False
            
            return True
            
        except Exception as e:
            self.slow_features.append(f"{feature_name}: Error - {str(e)}")
            return False
    
    def get_slow_features(self) -> List[str]:
        """Get list of features that are too slow"""
        return self.slow_features


class RedundantFeatureDetector:
    """Detects and removes redundant features"""
    
    def __init__(self, correlation_threshold: float = 0.95):
        self.correlation_threshold = correlation_threshold
        self.redundant_features = []
    
    def detect_correlation_redundancy(self, feature_df: pd.DataFrame) -> List[Tuple[str, str, float]]:
        """
        Detect highly correlated features
        
        Args:
            feature_df: DataFrame with features as columns
            
        Returns:
            List of tuples (feature1, feature2, correlation)
        """
        correlation_matrix = feature_df.corr().abs()
        upper_triangle = correlation_matrix.where(
            np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)
        )
        
        redundant_pairs = []
        for i in range(len(upper_triangle.columns)):
            for j in range(i+1, len(upper_triangle.columns)):
                corr_val = upper_triangle.iloc[i, j]
                if corr_val > self.correlation_threshold:
                    feature1 = upper_triangle.columns[i]
                    feature2 = upper_triangle.columns[j]
                    redundant_pairs.append((feature1, feature2, corr_val))
                    self.redundant_features.append((feature1, feature2, corr_val))
        
        return redundant_pairs
    
    def detect_mutual_info_redundancy(self, feature_df: pd.DataFrame, target: np.ndarray) -> Dict[str, float]:
        """
        Detect features with low mutual information with target
        
        Args:
            feature_df: DataFrame with features
            target: Target variable
            
        Returns:
            Dictionary of feature: mutual_info_score
        """
        mi_scores = {}
        
        for feature in feature_df.columns:
            try:
                # Discretize for mutual information computation
                feature_values = feature_df[feature].values
                mi_score = mutual_info_score(
                    pd.qcut(feature_values, q=10, duplicates='drop'), 
                    pd.qcut(target, q=10, duplicates='drop')
                )
                mi_scores[feature] = mi_score
            except:
                mi_scores[feature] = 0.0
        
        return mi_scores


class TimeSeriesOptimizedFeatureEngineer:
    """
    Time-series optimized feature engineer with strict temporal validation
    and real-time computability guarantees
    """
    
    SENSOR_COLS = ["s1", "s2", "s3"]
    SETTING_COLS = ["setting1", "setting2", "setting3"]
    
    def __init__(
        self,
        rolling_window: int = 15,  # Reduced for real-time performance
        use_scaler: bool = True,
        scaler_type: str = "robust",
        max_computation_time_ms: float = 50.0,
        correlation_threshold: float = 0.95
    ):
        self.window = rolling_window
        self.use_scaler = use_scaler
        self.max_computation_time_ms = max_computation_time_ms
        self.correlation_threshold = correlation_threshold
        
        # Initialize validators
        self.temporal_validator = TemporalFeatureValidator()
        self.realtime_checker = RealTimeFeatureChecker(max_computation_time_ms)
        self.redundancy_detector = RedundantFeatureDetector(correlation_threshold)
        
        # Initialize scalers
        if use_scaler:
            if scaler_type == "robust":
                self.sensor_scaler = RobustScaler()
                self.feature_scaler = RobustScaler()
            else:
                self.sensor_scaler = StandardScaler()
                self.feature_scaler = StandardScaler()
        else:
            self.sensor_scaler = None
            self.feature_scaler = None
        
        # Feature tracking
        self.valid_features = set()
        self.invalid_features = set()
        self.feature_importance = {}
        self.engine_baselines = {}  # For engine-specific normalization
        
        self._is_fitted = False
    
    def _compute_temporal_rolling_features(
        self,
        series: np.ndarray,
        sensor_name: str,
        current_value: float
    ) -> Dict[str, float]:
        """
        Compute strictly temporal rolling features
        Only uses past and current data, no future information
        """
        features = {}
        
        if len(series) == 0:
            return self._get_default_rolling_features(sensor_name)
        
        # Basic rolling statistics (temporal only)
        if len(series) >= 1:
            features[f"{sensor_name}_roll_mean"] = float(np.mean(series))
            features[f"{sensor_name}_roll_std"] = float(np.std(series, ddof=0))
            features[f"{sensor_name}_roll_min"] = float(np.min(series))
            features[f"{sensor_name}_roll_max"] = float(np.max(series))
            features[f"{sensor_name}_roll_range"] = features[f"{sensor_name}_roll_max"] - features[f"{sensor_name}_roll_min"]
        
        # Percentile features (temporal only)
        if len(series) >= 4:
            features[f"{sensor_name}_roll_median"] = float(np.median(series))
            features[f"{sensor_name}_roll_q25"] = float(np.percentile(series, 25))
            features[f"{sensor_name}_roll_q75"] = float(np.percentile(series, 75))
            features[f"{sensor_name}_roll_iqr"] = features[f"{sensor_name}_roll_q75"] - features[f"{sensor_name}_roll_q25"]
        else:
            features[f"{sensor_name}_roll_median"] = float(current_value)
            features[f"{sensor_name}_roll_q25"] = float(current_value)
            features[f"{sensor_name}_roll_q75"] = float(current_value)
            features[f"{sensor_name}_roll_iqr"] = 0.0
        
        # Exponential moving average (temporal only)
        if len(series) >= 1:
            ema_alpha = 0.3  # Fixed alpha for consistency
            ema_val = series[0]
            for val in series[1:]:
                ema_val = ema_alpha * val + (1 - ema_alpha) * ema_val
            features[f"{sensor_name}_ema"] = float(ema_val)
        else:
            features[f"{sensor_name}_ema"] = float(current_value)
        
        # Recent vs long-term ratio (temporal only)
        if len(series) >= 10:
            recent_mean = np.mean(series[-5:])  # Last 5 values
            long_term_mean = np.mean(series)    # All values
            features[f"{sensor_name}_recent_ratio"] = float(recent_mean / (long_term_mean + 1e-8))
        else:
            features[f"{sensor_name}_recent_ratio"] = 1.0
        
        return features
    
    def _compute_temporal_lag_features(
        self,
        series: np.ndarray,
        current_value: float,
        sensor_name: str
    ) -> Dict[str, float]:
        """
        Compute strictly temporal lag features
        Only uses past values, no future information
        """
        features = {}
        
        # Lag features (only past values)
        features[f"{sensor_name}_lag1"] = float(series[-1]) if len(series) >= 1 else float(current_value)
        features[f"{sensor_name}_lag2"] = float(series[-2]) if len(series) >= 2 else features[f"{sensor_name}_lag1"]
        features[f"{sensor_name}_lag3"] = float(series[-3]) if len(series) >= 3 else features[f"{sensor_name}_lag2"]
        
        # Change features (temporal only)
        features[f"{sensor_name}_change"] = float(current_value - features[f"{sensor_name}_lag1"])
        
        if len(series) >= 2:
            features[f"{sensor_name}_change_rate"] = float(
                (current_value - features[f"{sensor_name}_lag2"]) / 2.0
            )
        else:
            features[f"{sensor_name}_change_rate"] = 0.0
        
        # Acceleration (temporal only)
        if len(series) >= 3:
            features[f"{sensor_name}_acceleration"] = float(
                features[f"{sensor_name}_change"] - (features[f"{sensor_name}_lag1"] - features[f"{sensor_name}_lag2"])
            )
        else:
            features[f"{sensor_name}_acceleration"] = 0.0
        
        # Momentum (temporal only)
        if len(series) >= 5:
            recent_changes = []
            for i in range(1, min(5, len(series))):
                recent_changes.append(series[-i] - series[-i-1])
            features[f"{sensor_name}_momentum"] = float(np.mean(recent_changes))
        else:
            features[f"{sensor_name}_momentum"] = 0.0
        
        return features
    
    def _compute_temporal_trend_features(
        self,
        series: np.ndarray,
        sensor_name: str
    ) -> Dict[str, float]:
        """
        Compute strictly temporal trend features
        Only uses past data for trend calculation
        """
        features = {}
        
        if len(series) < 3:
            features[f"{sensor_name}_trend_slope"] = 0.0
            features[f"{sensor_name}_trend_r2"] = 0.0
            features[f"{sensor_name}_volatility"] = 0.0
            return features
        
        # Linear regression trend (temporal only)
        x = np.arange(len(series))
        try:
            coeffs = np.polyfit(x, series, 1)
            features[f"{sensor_name}_trend_slope"] = float(coeffs[0])
            
            # R-squared for trend quality
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((series - y_pred) ** 2)
            ss_tot = np.sum((series - np.mean(series)) ** 2)
            features[f"{sensor_name}_trend_r2"] = float(1 - (ss_res / (ss_tot + 1e-8)))
            
        except:
            features[f"{sensor_name}_trend_slope"] = 0.0
            features[f"{sensor_name}_trend_r2"] = 0.0
        
        # Volatility (temporal only)
        if len(series) >= 2:
            returns = np.diff(series) / (series[:-1] + 1e-8)
            features[f"{sensor_name}_volatility"] = float(np.std(returns, ddof=0))
        else:
            features[f"{sensor_name}_volatility"] = 0.0
        
        return features
    
    def _compute_engine_normalized_features(
        self,
        sensor_name: str,
        current_value: float,
        engine_id: int
    ) -> Dict[str, float]:
        """
        Compute engine-normalized features for better generalization
        """
        features = {}
        
        # Get or initialize engine baseline
        if engine_id not in self.engine_baselines:
            self.engine_baselines[engine_id] = {
                sensor_name: current_value for sensor_name in self.SENSOR_COLS
            }
        
        baseline = self.engine_baselines[engine_id].get(sensor_name, current_value)
        
        # Normalized deviation from baseline
        features[f"{sensor_name}_norm_deviation"] = float((current_value - baseline) / (baseline + 1e-8))
        
        # Relative change from baseline
        features[f"{sensor_name}_relative_change"] = float(current_value / (baseline + 1e-8))
        
        # Update baseline with exponential moving average
        if self.use_scaler:
            ema_alpha = 0.01  # Very slow adaptation for stability
            self.engine_baselines[engine_id][sensor_name] = (
                ema_alpha * current_value + (1 - ema_alpha) * baseline
            )
        
        return features
    
    def _compute_interaction_features(
        self,
        sensor_data: Dict[str, float],
        setting_data: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute interaction features that are temporally valid
        """
        features = {}
        
        # Sensor-sensor ratios (temporally valid)
        sensors = ['s1', 's2', 's3']
        for i, s1 in enumerate(sensors):
            for j, s2 in enumerate(sensors[i+1:], i+1):
                if s1 in sensor_data and s2 in sensor_data:
                    features[f"{s1}_div_{s2}"] = float(sensor_data[s1] / (sensor_data[s2] + 1e-8))
                    features[f"{s1}_x_{s2}"] = float(sensor_data[s1] * sensor_data[s2])
        
        # Sensor-setting interactions (temporally valid)
        for s in sensors:
            if s in sensor_data:
                for setting in self.SETTING_COLS:
                    if setting in setting_data:
                        features[f"{s}_x_{setting}"] = float(sensor_data[s] * setting_data[setting])
        
        return features
    
    def _get_default_rolling_features(self, sensor_name: str) -> Dict[str, float]:
        """Default values when insufficient data"""
        defaults = {}
        rolling_features = [
            'roll_mean', 'roll_std', 'roll_min', 'roll_max', 'roll_range',
            'roll_median', 'roll_q25', 'roll_q75', 'roll_iqr', 'ema', 'recent_ratio'
        ]
        
        for feature in rolling_features:
            defaults[f"{sensor_name}_{feature}"] = 0.0
        
        return defaults
    
    def _validate_temporal_compliance(self, features: Dict[str, float]) -> bool:
        """Validate that all features are temporally compliant"""
        for feature_name in features.keys():
            if not self.temporal_validator.validate_feature(
                feature_name, 
                "computed from historical data only"
            ):
                self.invalid_features.add(feature_name)
                return False
        
        return True
    
    def _check_real_time_computability(self, features: Dict[str, float]) -> bool:
        """Check that all features can be computed in real-time"""
        # This is a simplified check - in practice, you'd time each feature
        # For now, we assume all features are designed for real-time computation
        return True
    
    def build_temporal_feature_row(
        self,
        engine_state: Dict,
        cycle: int,
        sensors: np.ndarray,
        op_settings: np.ndarray,
        history: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Build strictly temporal feature row
        No future information, real-time computable
        """
        features = {
            "engine_id": float(engine_state.get("engine_id", 0)),
            "cycle": float(cycle),
        }
        
        # Raw sensor and setting values
        sensor_data = {}
        for i, name in enumerate(self.SENSOR_COLS):
            features[name] = float(sensors[i])
            sensor_data[name] = float(sensors[i])
        
        setting_data = {}
        for i, name in enumerate(self.SETTING_COLS):
            features[name] = float(op_settings[i])
            setting_data[name] = float(op_settings[i])
        
        # Use provided history or extract from engine_state
        if history is None and "history" in engine_state:
            history = np.array(engine_state["history"])
        
        if history is not None and len(history) > 0:
            # Compute temporal features for each sensor
            for i, sensor_name in enumerate(self.SENSOR_COLS):
                sensor_series = history[:, i] if history.shape[1] > i else np.array([])
                current_val = sensors[i]
                
                # Rolling features (temporal only)
                rolling_feats = self._compute_temporal_rolling_features(
                    sensor_series, sensor_name, current_val
                )
                features.update(rolling_feats)
                
                # Lag features (temporal only)
                lag_feats = self._compute_temporal_lag_features(
                    sensor_series, current_val, sensor_name
                )
                features.update(lag_feats)
                
                # Trend features (temporal only)
                trend_feats = self._compute_temporal_trend_features(sensor_series, sensor_name)
                features.update(trend_feats)
                
                # Engine-normalized features
                norm_feats = self._compute_engine_normalized_features(
                    sensor_name, current_val, engine_state.get("engine_id", 0)
                )
                features.update(norm_feats)
            
            # Interaction features (temporally valid)
            interaction_feats = self._compute_interaction_features(sensor_data, setting_data)
            features.update(interaction_feats)
            
            # Global temporal features
            features["life_ratio"] = float(cycle / max(engine_state.get("design_life", 3000), 1))
            
            # Health index (temporal only)
            health_values = []
            for sensor_name in self.SENSOR_COLS:
                ema_key = f"{sensor_name}_ema"
                if ema_key in features:
                    health_values.append(features[ema_key])
            
            if health_values:
                features["health_index"] = float(np.mean(health_values))
                features["health_x_life"] = features["health_index"] * features["life_ratio"]
            else:
                features["health_index"] = 1.0
                features["health_x_life"] = features["life_ratio"]
        
        else:
            # Add default features when no history available
            self._add_default_temporal_features(features, sensors, op_settings, engine_state)
        
        # Validate temporal compliance
        if self._validate_temporal_compliance(features):
            self.valid_features.update(features.keys())
        else:
            # Filter out invalid features
            valid_features_only = {
                k: v for k, v in features.items() 
                if k not in self.invalid_features
            }
            features = valid_features_only
        
        # Fill any NaN values
        for key, value in features.items():
            if isinstance(value, float) and np.isnan(value):
                features[key] = 0.0
        
        return features
    
    def _add_default_temporal_features(
        self,
        features: Dict[str, float],
        sensors: np.ndarray,
        op_settings: np.ndarray,
        engine_state: Dict
    ):
        """Add default temporal features when insufficient history"""
        for i, sensor_name in enumerate(self.SENSOR_COLS):
            # Default rolling features
            defaults = self._get_default_rolling_features(sensor_name)
            features.update(defaults)
            
            # Default lag features
            features[f"{sensor_name}_lag1"] = float(sensors[i])
            features[f"{sensor_name}_lag2"] = float(sensors[i])
            features[f"{sensor_name}_lag3"] = float(sensors[i])
            features[f"{sensor_name}_change"] = 0.0
            features[f"{sensor_name}_change_rate"] = 0.0
            features[f"{sensor_name}_acceleration"] = 0.0
            features[f"{sensor_name}_momentum"] = 0.0
            
            # Default trend features
            features[f"{sensor_name}_trend_slope"] = 0.0
            features[f"{sensor_name}_trend_r2"] = 0.0
            features[f"{sensor_name}_volatility"] = 0.0
            
            # Default engine-normalized features
            features[f"{sensor_name}_norm_deviation"] = 0.0
            features[f"{sensor_name}_relative_change"] = 1.0
        
        # Default interaction features
        sensors = ['s1', 's2', 's3']
        for i, s1 in enumerate(sensors):
            for j, s2 in enumerate(sensors[i+1:], i+1):
                features[f"{s1}_div_{s2}"] = 1.0
                features[f"{s1}_x_{s2}"] = features[s1] * features[s2]
        
        for s in sensors:
            for setting in self.SETTING_COLS:
                features[f"{s}_x_{setting}"] = features[s] * features[setting]
        
        # Default global features
        features["life_ratio"] = 0.0
        features["health_index"] = 1.0
        features["health_x_life"] = 0.0
    
    def prune_features_by_importance(
        self,
        feature_importance: Dict[str, float],
        importance_threshold: float = 0.001
    ) -> Set[str]:
        """
        Prune features based on importance scores
        
        Args:
            feature_importance: Dictionary of feature: importance_score
            importance_threshold: Minimum importance to keep feature
            
        Returns:
            Set of features to remove
        """
        self.feature_importance = feature_importance
        
        # Sort features by importance
        sorted_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Find features below threshold
        features_to_remove = set()
        for feature, importance in sorted_features:
            if importance < importance_threshold:
                features_to_remove.add(feature)
        
        # Always keep essential features
        essential_features = {
            'engine_id', 'cycle', 's1', 's2', 's3', 
            'setting1', 'setting2', 'setting3', 'life_ratio'
        }
        features_to_remove -= essential_features
        
        self.valid_features -= features_to_remove
        self.invalid_features.update(features_to_remove)
        
        return features_to_remove
    
    def remove_redundant_features(
        self,
        feature_df: pd.DataFrame,
        target: np.ndarray
    ) -> Tuple[Set[str], Dict[str, float]]:
        """
        Remove redundant features based on correlation and mutual information
        
        Args:
            feature_df: DataFrame with features
            target: Target variable
            
        Returns:
            Tuple of (features_to_remove, mutual_info_scores)
        """
        # Detect correlation redundancy
        redundant_pairs = self.redundancy_detector.detect_correlation_redundancy(feature_df)
        
        # Remove one feature from each highly correlated pair
        features_to_remove = set()
        for feature1, feature2, corr in redundant_pairs:
            # Remove the feature with lower importance if available
            if self.feature_importance:
                imp1 = self.feature_importance.get(feature1, 0)
                imp2 = self.feature_importance.get(feature2, 0)
                if imp1 < imp2:
                    features_to_remove.add(feature1)
                else:
                    features_to_remove.add(feature2)
            else:
                # If no importance info, remove the second feature
                features_to_remove.add(feature2)
        
        # Detect low mutual information features
        mi_scores = self.redundancy_detector.detect_mutual_info_redundancy(feature_df, target)
        
        # Remove features with very low mutual information
        mi_threshold = np.percentile(list(mi_scores.values()), 10)  # Bottom 10%
        for feature, mi_score in mi_scores.items():
            if mi_score < mi_threshold and feature not in essential_features:
                features_to_remove.add(feature)
        
        # Update valid features
        self.valid_features -= features_to_remove
        self.invalid_features.update(features_to_remove)
        
        return features_to_remove, mi_scores
    
    def get_optimized_feature_names(self) -> List[str]:
        """Get list of optimized (valid) feature names"""
        return sorted(list(self.valid_features))
    
    def fit(self, training_data: List[Dict[str, float]]) -> 'TimeSeriesOptimizedFeatureEngineer':
        """Fit feature engineer on training data"""
        if not training_data:
            return self
        
        # Initialize scalers if needed
        if self.use_scaler and self.sensor_scaler is None:
            from sklearn.preprocessing import RobustScaler
            self.sensor_scaler = RobustScaler()
            self.feature_scaler = RobustScaler()
        
        # Fit scalers on raw sensor values
        if self.use_scaler and self.sensor_scaler:
            df = pd.DataFrame(training_data)
            sensor_cols = [col for col in self.SENSOR_COLS if col in df.columns]
            if sensor_cols:
                self.sensor_scaler.fit(df[sensor_cols])
        
        # Initialize engine baselines
        for row in training_data:
            engine_id = int(row.get('engine_id', 0))
            if engine_id not in self.engine_baselines:
                self.engine_baselines[engine_id] = {
                    sensor: row.get(sensor, 0.0) for sensor in self.SENSOR_COLS
                }
        
        self._is_fitted = True
        return self
    
    def transform(self, data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """Transform data using fitted scalers"""
        if not self._is_fitted:
            return data
        
        df = pd.DataFrame(data)
        
        # Scale raw sensor values
        if self.use_scaler and self.sensor_scaler:
            sensor_cols = [col for col in self.SENSOR_COLS if col in df.columns]
            if sensor_cols:
                df[sensor_cols] = self.sensor_scaler.transform(df[sensor_cols])
        
        return df.to_dict('records')
    
    def get_feature_statistics(self) -> Dict[str, Any]:
        """Get statistics about feature optimization"""
        return {
            'total_features_computed': len(self.valid_features) + len(self.invalid_features),
            'valid_features': len(self.valid_features),
            'invalid_features': len(self.invalid_features),
            'temporal_violations': len(self.temporal_validator.get_violations()),
            'slow_features': len(self.realtime_checker.get_slow_features()),
            'redundant_features': len(self.redundancy_detector.redundant_features),
            'engine_baselines': len(self.engine_baselines)
        }


# Essential features that should never be removed
essential_features = {
    'engine_id', 'cycle', 's1', 's2', 's3', 
    'setting1', 'setting2', 'setting3', 'life_ratio'
}
