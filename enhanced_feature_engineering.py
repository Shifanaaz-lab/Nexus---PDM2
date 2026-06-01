"""
Enhanced Feature Engineering for Predictive Maintenance
Production-ready time-series feature extraction with streaming compatibility
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from collections import deque
from sklearn.preprocessing import StandardScaler, RobustScaler
import warnings
warnings.filterwarnings('ignore')


class EnhancedFeatureEngineer:
    """
    Production-grade feature engineering for RUL prediction.
    
    Key improvements:
    - Advanced time-series features (FFT, wavelet-inspired features)
    - Proper scaling and normalization
    - Streaming-compatible computation
    - Temporal dependency handling per engine
    - Statistical robustness measures
    """
    
    SENSOR_COLS = ["s1", "s2", "s3"]
    SETTING_COLS = ["setting1", "setting2", "setting3"]
    
    def __init__(
        self, 
        rolling_window: int = 30,  # Increased for better trend detection
        use_scaler: bool = True,
        scaler_type: str = "robust"  # robust to outliers
    ):
        self.window = rolling_window
        self.use_scaler = use_scaler
        
        # Initialize scalers for different feature groups
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
            
        # Feature groups for organized processing
        self.feature_groups = {
            'raw': self.SENSOR_COLS + self.SETTING_COLS,
            'rolling': [],
            'lag': [],
            'trend': [],
            'frequency': [],
            'statistical': [],
            'interaction': []
        }
        
        self._is_fitted = False
    
    def _compute_advanced_rolling_features(
        self, 
        series: np.ndarray, 
        sensor_name: str
    ) -> Dict[str, float]:
        """Compute advanced rolling statistics"""
        features = {}
        
        if len(series) < 2:
            return self._get_default_rolling_features(sensor_name)
        
        w = min(self.window, len(series))
        window_vals = series[-w:]
        
        # Basic rolling statistics
        features[f"{sensor_name}_roll_mean"] = float(np.mean(window_vals))
        features[f"{sensor_name}_roll_std"] = float(np.std(window_vals, ddof=0))
        features[f"{sensor_name}_roll_var"] = float(np.var(window_vals, ddof=0))
        features[f"{sensor_name}_roll_min"] = float(np.min(window_vals))
        features[f"{sensor_name}_roll_max"] = float(np.max(window_vals))
        features[f"{sensor_name}_roll_range"] = features[f"{sensor_name}_roll_max"] - features[f"{sensor_name}_roll_min"]
        
        # Percentile-based features (robust to outliers)
        features[f"{sensor_name}_roll_median"] = float(np.median(window_vals))
        features[f"{sensor_name}_roll_q25"] = float(np.percentile(window_vals, 25))
        features[f"{sensor_name}_roll_q75"] = float(np.percentile(window_vals, 75))
        features[f"{sensor_name}_roll_iqr"] = features[f"{sensor_name}_roll_q75"] - features[f"{sensor_name}_roll_q25"]
        
        # Distribution shape (if enough data)
        if len(window_vals) >= 4:
            pd_series = pd.Series(window_vals)
            features[f"{sensor_name}_roll_skew"] = float(pd_series.skew())
            features[f"{sensor_name}_roll_kurtosis"] = float(pd_series.kurtosis())
        else:
            features[f"{sensor_name}_roll_skew"] = 0.0
            features[f"{sensor_name}_roll_kurtosis"] = 0.0
        
        # Exponential Moving Average (multiple alphas for different sensitivity)
        for alpha in [0.1, 0.3, 0.5]:
            ema_val = window_vals[0]
            for val in window_vals[1:]:
                ema_val = alpha * val + (1 - alpha) * ema_val
            features[f"{sensor_name}_ema_{alpha}"] = float(ema_val)
        
        return features
    
    def _compute_lag_features(
        self, 
        series: np.ndarray, 
        current_val: float,
        sensor_name: str
    ) -> Dict[str, float]:
        """Compute lag-based features"""
        features = {}
        
        if len(series) == 0:
            features[f"{sensor_name}_lag1"] = 0.0
            features[f"{sensor_name}_lag2"] = 0.0
            features[f"{sensor_name}_lag3"] = 0.0
            features[f"{sensor_name}_change"] = 0.0
            features[f"{sensor_name}_change_rate"] = 0.0
            features[f"{sensor_name}_acceleration"] = 0.0
            return features
        
        # Lag values
        features[f"{sensor_name}_lag1"] = float(series[-1]) if len(series) >= 1 else 0.0
        features[f"{sensor_name}_lag2"] = float(series[-2]) if len(series) >= 2 else 0.0
        features[f"{sensor_name}_lag3"] = float(series[-3]) if len(series) >= 3 else 0.0
        
        # Change features
        features[f"{sensor_name}_change"] = float(current_val - features[f"{sensor_name}_lag1"])
        
        if len(series) >= 2:
            features[f"{sensor_name}_change_rate"] = float(
                (current_val - features[f"{sensor_name}_lag2"]) / 2.0
            )
            features[f"{sensor_name}_acceleration"] = float(
                features[f"{sensor_name}_change"] - (features[f"{sensor_name}_lag1"] - features[f"{sensor_name}_lag2"])
            )
        else:
            features[f"{sensor_name}_change_rate"] = 0.0
            features[f"{sensor_name}_acceleration"] = 0.0
        
        return features
    
    def _compute_trend_features(
        self, 
        series: np.ndarray, 
        sensor_name: str
    ) -> Dict[str, float]:
        """Compute trend and momentum features"""
        features = {}
        
        if len(series) < 3:
            features[f"{sensor_name}_trend_slope"] = 0.0
            features[f"{sensor_name}_trend_r2"] = 0.0
            features[f"{sensor_name}_momentum"] = 0.0
            return features
        
        # Linear regression trend
        x = np.arange(len(series))
        coeffs = np.polyfit(x, series, 1)
        features[f"{sensor_name}_trend_slope"] = float(coeffs[0])
        
        # R-squared for trend quality
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((series - y_pred) ** 2)
        ss_tot = np.sum((series - np.mean(series)) ** 2)
        features[f"{sensor_name}_trend_r2"] = float(1 - (ss_res / (ss_tot + 1e-8)))
        
        # Momentum (recent slope vs long-term slope)
        if len(series) >= 6:
            recent_x = np.arange(len(series) - 3, len(series))
            recent_series = series[-3:]
            recent_coeffs = np.polyfit(recent_x, recent_series, 1)
            features[f"{sensor_name}_momentum"] = float(recent_coeffs[0] - coeffs[0])
        else:
            features[f"{sensor_name}_momentum"] = 0.0
        
        return features
    
    def _compute_frequency_features(
        self, 
        series: np.ndarray, 
        sensor_name: str
    ) -> Dict[str, float]:
        """Compute frequency-domain features"""
        features = {}
        
        if len(series) < 4:
            features[f"{sensor_name}_fft_energy"] = 0.0
            features[f"{sensor_name}_fft_dominant_freq"] = 0.0
            features[f"{sensor_name}_spectral_centroid"] = 0.0
            return features
        
        # FFT-based features
        fft_vals = np.fft.fft(series)
        fft_energy = np.sum(np.abs(fft_vals) ** 2)
        features[f"{sensor_name}_fft_energy"] = float(fft_energy)
        
        # Dominant frequency
        freqs = np.fft.fftfreq(len(series))
        dominant_freq_idx = np.argmax(np.abs(fft_vals[1:len(fft_vals)//2])) + 1
        features[f"{sensor_name}_fft_dominant_freq"] = float(abs(freqs[dominant_freq_idx]))
        
        # Spectral centroid (frequency weighted center)
        magnitudes = np.abs(fft_vals[:len(fft_vals)//2])
        freqs_half = freqs[:len(freqs)//2]
        if np.sum(magnitudes) > 0:
            features[f"{sensor_name}_spectral_centroid"] = float(
                np.sum(freqs_half * magnitudes) / np.sum(magnitudes)
            )
        else:
            features[f"{sensor_name}_spectral_centroid"] = 0.0
        
        return features
    
    def _compute_statistical_features(
        self, 
        series: np.ndarray, 
        sensor_name: str
    ) -> Dict[str, float]:
        """Compute statistical robustness features"""
        features = {}
        
        if len(series) < 2:
            features[f"{sensor_name}_cv"] = 0.0  # Coefficient of variation
            features[f"{sensor_name}_zscore_current"] = 0.0
            features[f"{sensor_name}_outlier_count"] = 0.0
            return features
        
        # Coefficient of variation
        mean_val = np.mean(series)
        std_val = np.std(series, ddof=0)
        features[f"{sensor_name}_cv"] = float(std_val / (abs(mean_val) + 1e-8))
        
        # Current value z-score
        current_val = series[-1]
        features[f"{sensor_name}_zscore_current"] = float(
            (current_val - mean_val) / (std_val + 1e-8)
        )
        
        # Outlier count (beyond 2 std)
        outliers = np.abs((series - mean_val) / (std_val + 1e-8)) > 2
        features[f"{sensor_name}_outlier_count"] = float(np.sum(outliers))
        
        return features
    
    def _compute_interaction_features(
        self, 
        sensor_data: Dict[str, float],
        setting_data: Dict[str, float]
    ) -> Dict[str, float]:
        """Compute cross-sensor and sensor-setting interactions"""
        features = {}
        
        # Sensor-sensor interactions
        sensors = ['s1', 's2', 's3']
        for i, s1 in enumerate(sensors):
            for j, s2 in enumerate(sensors[i+1:], i+1):
                if f"{s1}" in sensor_data and f"{s2}" in sensor_data:
                    features[f"{s1}_x_{s2}"] = sensor_data[f"{s1}"] * sensor_data[f"{s2}"]
                    features[f"{s1}_div_{s2}"] = sensor_data[f"{s1}"] / (sensor_data[f"{s2}"] + 1e-8)
        
        # Sensor-setting interactions
        for s in sensors:
            if f"{s}" in sensor_data:
                for setting in ['setting1', 'setting2', 'setting3']:
                    if setting in setting_data:
                        features[f"{s}_x_{setting}"] = sensor_data[f"{s}"] * setting_data[setting]
        
        return features
    
    def _get_default_rolling_features(self, sensor_name: str) -> Dict[str, float]:
        """Default values when insufficient data"""
        defaults = {}
        prefixes = ['roll_mean', 'roll_std', 'roll_var', 'roll_min', 'roll_max', 
                   'roll_range', 'roll_median', 'roll_q25', 'roll_q75', 'roll_iqr',
                   'roll_skew', 'roll_kurtosis']
        for prefix in prefixes:
            defaults[f"{sensor_name}_{prefix}"] = 0.0
        
        # EMA defaults
        for alpha in [0.1, 0.3, 0.5]:
            defaults[f"{sensor_name}_ema_{alpha}"] = 0.0
        
        return defaults
    
    def _compute_health_index(self, sensor_features: Dict[str, float]) -> float:
        """Compute enhanced health index using multiple indicators"""
        health_indicators = []
        
        # Use EMA values as they're more stable
        for sensor in self.SENSOR_COLS:
            ema_key = f"{sensor}_ema_0.3"
            if ema_key in sensor_features:
                health_indicators.append(sensor_features[ema_key])
        
        if not health_indicators:
            return 1.0
        
        # Robust health index (median-based)
        health_median = np.median(health_indicators)
        
        # Normalize by baseline (will be set during fitting)
        if hasattr(self, '_baseline_health'):
            health_index = health_median / self._baseline_health
        else:
            health_index = 1.0
        
        return float(np.clip(health_index, 0.0, 2.0))
    
    def fit(self, training_data: List[Dict[str, float]]) -> 'EnhancedFeatureEngineer':
        """Fit scalers and compute baselines on training data"""
        if not training_data:
            return self
        
        df = pd.DataFrame(training_data)
        
        # Fit sensor scaler on raw sensor values
        if self.use_scaler and self.sensor_scaler:
            sensor_cols = [col for col in self.SENSOR_COLS if col in df.columns]
            if sensor_cols:
                self.sensor_scaler.fit(df[sensor_cols])
        
        # Fit feature scaler on engineered features (excluding identifiers)
        if self.use_scaler and self.feature_scaler:
            feature_cols = [col for col in df.columns 
                          if col not in ['engine_id', 'cycle'] and 
                             not any(col.startswith(s) for s in self.SENSOR_COLS + self.SETTING_COLS)]
            if feature_cols:
                self.feature_scaler.fit(df[feature_cols])
        
        # Compute baseline health index
        health_values = []
        for row in training_data:
            sensor_features = {k: v for k, v in row.items() 
                             if any(k.startswith(s) for s in self.SENSOR_COLS)}
            if sensor_features:
                health_values.append(np.mean(list(sensor_features.values())))
        
        if health_values:
            self._baseline_health = np.median(health_values)
        else:
            self._baseline_health = 1.0
        
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
        
        # Scale engineered features
        if self.use_scaler and self.feature_scaler:
            feature_cols = [col for col in df.columns 
                          if col not in ['engine_id', 'cycle'] and 
                             not any(col.startswith(s) for s in self.SENSOR_COLS + self.SETTING_COLS)]
            if feature_cols:
                df[feature_cols] = self.feature_scaler.transform(df[feature_cols])
        
        return df.to_dict('records')
    
    def build_feature_row(
        self,
        engine_state: Dict,
        cycle: int,
        sensors: np.ndarray,
        op_settings: np.ndarray,
        history: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Build comprehensive feature row for a single engine reading.
        
        Args:
            engine_state: Dictionary containing engine metadata
            cycle: Current cycle number
            sensors: Current sensor readings
            op_settings: Current operational settings
            history: Historical sensor data (optional)
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
            # Compute all feature groups
            for i, sensor_name in enumerate(self.SENSOR_COLS):
                sensor_series = history[:, i] if history.shape[1] > i else np.array([])
                current_val = sensors[i]
                
                # Rolling features
                rolling_feats = self._compute_advanced_rolling_features(sensor_series, sensor_name)
                features.update(rolling_feats)
                
                # Lag features
                lag_feats = self._compute_lag_features(sensor_series, current_val, sensor_name)
                features.update(lag_feats)
                
                # Trend features
                trend_feats = self._compute_trend_features(sensor_series, sensor_name)
                features.update(trend_feats)
                
                # Frequency features
                freq_feats = self._compute_frequency_features(sensor_series, sensor_name)
                features.update(freq_feats)
                
                # Statistical features
                stat_feats = self._compute_statistical_features(sensor_series, sensor_name)
                features.update(stat_feats)
            
            # Interaction features
            interaction_feats = self._compute_interaction_features(sensor_data, setting_data)
            features.update(interaction_feats)
            
            # Enhanced health index
            health_index = self._compute_health_index(sensor_data)
            features["health_index"] = health_index
            
            # Life ratio and related features
            design_life = engine_state.get("design_life", 3000)
            life_ratio = cycle / max(design_life, 1)
            features["life_ratio"] = float(np.clip(life_ratio, 0.0, 2.0))
            features["health_x_life"] = health_index * life_ratio
            features["health_x_cycle"] = health_index * cycle
            
            # Degradation rate features
            if len(history) >= 10:
                # Recent degradation vs long-term degradation
                recent_history = history[-5:]
                long_term_history = history
                
                recent_degradation = np.mean(recent_history, axis=0)
                long_term_degradation = np.mean(long_term_history, axis=0)
                
                for i, sensor_name in enumerate(self.SENSOR_COLS):
                    if i < len(recent_degradation):
                        degradation_ratio = recent_degradation[i] / (long_term_degradation[i] + 1e-8)
                        features[f"{sensor_name}_degradation_ratio"] = float(degradation_ratio)
        else:
            # Default values when no history available
            self._add_default_features(features)
        
        # Fill any NaN values
        for key, value in features.items():
            if isinstance(value, float) and np.isnan(value):
                features[key] = 0.0
        
        return features
    
    def _add_default_features(self, features: Dict[str, float]):
        """Add default feature values when insufficient data"""
        # Default rolling features
        for sensor in self.SENSOR_COLS:
            rolling_defaults = self._get_default_rolling_features(sensor)
            features.update(rolling_defaults)
            
            # Default lag features
            features[f"{sensor}_lag1"] = 0.0
            features[f"{sensor}_lag2"] = 0.0
            features[f"{sensor}_lag3"] = 0.0
            features[f"{sensor}_change"] = 0.0
            features[f"{sensor}_change_rate"] = 0.0
            features[f"{sensor}_acceleration"] = 0.0
            
            # Default trend features
            features[f"{sensor}_trend_slope"] = 0.0
            features[f"{sensor}_trend_r2"] = 0.0
            features[f"{sensor}_momentum"] = 0.0
            
            # Default frequency features
            features[f"{sensor}_fft_energy"] = 0.0
            features[f"{sensor}_fft_dominant_freq"] = 0.0
            features[f"{sensor}_spectral_centroid"] = 0.0
            
            # Default statistical features
            features[f"{sensor}_cv"] = 0.0
            features[f"{sensor}_zscore_current"] = 0.0
            features[f"{sensor}_outlier_count"] = 0.0
        
        # Default health and life features
        features["health_index"] = 1.0
        features["life_ratio"] = 0.0
        features["health_x_life"] = 0.0
        features["health_x_cycle"] = 0.0
    
    def get_feature_names(self) -> List[str]:
        """Get list of all feature names this engineer can produce"""
        feature_names = ['engine_id', 'cycle']
        
        # Raw features
        feature_names.extend(self.SENSOR_COLS + self.SETTING_COLS)
        
        # All engineered features
        for sensor in self.SENSOR_COLS:
            # Rolling features
            rolling_prefixes = ['roll_mean', 'roll_std', 'roll_var', 'roll_min', 'roll_max',
                               'roll_range', 'roll_median', 'roll_q25', 'roll_q75', 'roll_iqr',
                               'roll_skew', 'roll_kurtosis']
            for prefix in rolling_prefixes:
                feature_names.append(f"{sensor}_{prefix}")
            
            # EMA features
            for alpha in [0.1, 0.3, 0.5]:
                feature_names.append(f"{sensor}_ema_{alpha}")
            
            # Lag features
            lag_prefixes = ['lag1', 'lag2', 'lag3', 'change', 'change_rate', 'acceleration']
            for prefix in lag_prefixes:
                feature_names.append(f"{sensor}_{prefix}")
            
            # Trend features
            trend_prefixes = ['trend_slope', 'trend_r2', 'momentum']
            for prefix in trend_prefixes:
                feature_names.append(f"{sensor}_{prefix}")
            
            # Frequency features
            freq_prefixes = ['fft_energy', 'fft_dominant_freq', 'spectral_centroid']
            for prefix in freq_prefixes:
                feature_names.append(f"{sensor}_{prefix}")
            
            # Statistical features
            stat_prefixes = ['cv', 'zscore_current', 'outlier_count', 'degradation_ratio']
            for prefix in stat_prefixes:
                feature_names.append(f"{sensor}_{prefix}")
        
        # Interaction features
        sensors = ['s1', 's2', 's3']
        for i, s1 in enumerate(sensors):
            for j, s2 in enumerate(sensors[i+1:], i+1):
                feature_names.extend([f"{s1}_x_{s2}", f"{s1}_div_{s2}"])
        
        for s in sensors:
            for setting in self.SETTING_COLS:
                feature_names.append(f"{s}_x_{setting}")
        
        # Health and life features
        health_features = ['health_index', 'life_ratio', 'health_x_life', 'health_x_cycle']
        feature_names.extend(health_features)
        
        return feature_names
