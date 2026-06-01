import os
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Tuple

import numpy as np
import pandas as pd
from pymongo import MongoClient
from xgboost import XGBRegressor
import joblib


ROLLING_WINDOW = 15  # Increased for smoother EMA/SMA
EMA_ALPHA = 0.2     # Smoother weighting for recent data
MAX_RUL_CAP = 125   # Piecewise RUL limit (industry standard)
NUM_ENGINES = 100
BATCH_INTERVAL_SECONDS = 0.1

# New configurable parameters for realistic degradation
BURST_INTERVAL = int(os.getenv('BURST_INTERVAL', '250'))  # cycles between stress bursts
BURST_PERCENTAGE = float(os.getenv('BURST_PERCENTAGE', '0.07'))  # % of fleet hit per burst
BURST_MULTIPLIER = float(os.getenv('BURST_MULTIPLIER', '2.5'))  # how much degradation_rate spikes

WEIBULL_BETA = float(os.getenv('WEIBULL_BETA', '1.8'))
WEIBULL_SCALE = float(os.getenv('WEIBULL_SCALE', '0.8'))  # fraction of design life


# Absolute RUL-based failure and risk (tunable via env)
FAILURE_RUL_THRESHOLD = float(os.getenv("FAILURE_RUL_THRESHOLD", "100"))   # RUL < this → engine failed, replace
# Increase denominator so risk rises more slowly (realistic for large fleets)
CRITICAL_RUL_FOR_RISK = float(os.getenv("CRITICAL_RUL_FOR_RISK", "800"))   # failure_prob = 1 - RUL/this (larger value → flatter curve)
# Move critical band farther to the right (less aggressive)
HIGH_WARNING_THRESHOLD = float(os.getenv("WARNING_THRESHOLD", "0.6"))           # warning band: prob in (this, HIGH_RISK]
HIGH_RISK_THRESHOLD = float(os.getenv("HIGH_RISK_THRESHOLD", "0.8"))        # critical band: prob > this, HIGH_RISK]


def _safe_positive(values: np.ndarray) -> np.ndarray:
    return np.clip(values, a_min=0.0, a_max=None)


@dataclass
class EngineState:
    engine_id: int
    cycle: int = 0
    base_sensors: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    degradation_rate: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    # Quadratic acceleration factor for each sensor (creates wear‑out acceleration)
    accel_factor: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))
    # Temporary multiplier applied during stress‑burst events
    burst_multiplier: float = 1.0
    history: Deque[np.ndarray] = field(default_factory=lambda: deque(maxlen=ROLLING_WINDOW))
    design_life: int = 3000

    def initialize_random(self, rng: np.random.Generator) -> None:
        # Three synthetic sensors with different nominal ranges
        self.base_sensors = rng.uniform([20.0, 600.0, 900.0], [50.0, 800.0, 1100.0])
        # Per‑cycle degradation (linear term)
        self.degradation_rate = rng.uniform([0.001, 0.02, 0.03], [0.01, 0.05, 0.06])
        # Quadratic acceleration term – small value that grows with cycle²
        self.accel_factor = rng.uniform([0.0, 0.0, 0.0], [5e-5, 5e-5, 5e-5])
        # Reset any burst multiplier
        self.burst_multiplier = 1.0
        self.design_life = int(rng.integers(2000, 4000))

    def next_reading(self, rng: np.random.Generator) -> Tuple[int, np.ndarray, np.ndarray]:
        self.cycle += 1

        # Apply burst multiplier to the linear part only
        effective_rate = self.degradation_rate * self.burst_multiplier
        # Quadratic acceleration always applied
        degradation = effective_rate * self.cycle + self.accel_factor * (self.cycle ** 2)
        noise = rng.normal(loc=0.0, scale=[0.2, 1.0, 1.5], size=3)
        sensors = self.base_sensors - degradation + noise
        sensors = _safe_positive(sensors)
        # Reset burst multiplier after this reading so the effect lasts one cycle
        self.burst_multiplier = 1.0

        # Operational settings (3)
        op_settings = np.array(
            [
                rng.uniform(0.0, 1.0),      # setting 1
                rng.uniform(20.0, 40.0),    # setting 2 (e.g. temp)
                rng.uniform(900.0, 1100.0), # setting 3 (e.g. RPM)
            ],
            dtype=float,
        )

        self.history.append(sensors.copy())
        return self.cycle, sensors, op_settings


class FeatureEngineer:
    """
    Applies feature engineering consistent with model training.

    Features per sensor s{i}:
      - rolling mean/std over last ROLLING_WINDOW cycles
      - lag1, lag2
      - change = current - lag1
      - trend = slope from linear regression over window

    Global per‑engine features:
      - health_index: normalized combination of sensors
      - life_ratio: cycle / design_life
    """

    SENSOR_COLS = ["s1", "s2", "s3"]
    SETTING_COLS = ["setting1", "setting2", "setting3"]

    def __init__(self, rolling_window: int = ROLLING_WINDOW) -> None:
        self.window = rolling_window

    def _compute_sensor_features(self, engine: EngineState, current_sensors: np.ndarray) -> Dict[str, float]:
        hist = np.array(engine.history)
        features: Dict[str, float] = {}

        for i, s_name in enumerate(self.SENSOR_COLS):
            series = hist[:, i] if hist.shape[0] > 0 else np.array([], dtype=float)

            # rolling mean/std (SMA)
            if series.size >= 1:
                w = min(self.window, series.size)
                window_vals = series[-w:]
                features[f"{s_name}_roll_mean"] = float(window_vals.mean())
                features[f"{s_name}_roll_std"] = float(window_vals.std(ddof=0))
                
                # Distribution shape features (industrial standard)
                if series.size >= 4:
                    pd_series = pd.Series(window_vals)
                    features[f"{s_name}_skew"] = float(pd_series.skew())
                    features[f"{s_name}_kurtosis"] = float(pd_series.kurt())
                else:
                    features[f"{s_name}_skew"] = 0.0
                    features[f"{s_name}_kurtosis"] = 0.0

                # EMA Filtering (New industrial-grade signal)
                ema_val = series[0]
                for val in series[1:]:
                    ema_val = EMA_ALPHA * val + (1 - EMA_ALPHA) * ema_val
                features[f"{s_name}_ema"] = float(ema_val)
            else:
                features[f"{s_name}_roll_mean"] = 0.0
                features[f"{s_name}_roll_std"] = 0.0
                features[f"{s_name}_skew"] = 0.0
                features[f"{s_name}_kurtosis"] = 0.0
                features[f"{s_name}_ema"] = 0.0

            # lags
            features[f"{s_name}_lag1"] = float(series[-1]) if series.size >= 1 else 0.0
            features[f"{s_name}_lag2"] = float(series[-2]) if series.size >= 2 else 0.0

            # change & accel
            features[f"{s_name}_change"] = float(current_sensors[i] - features[f"{s_name}_lag1"])
            features[f"{s_name}_accel"] = features[f"{s_name}_change"] - (features[f"{s_name}_lag1"] - features[f"{s_name}_lag2"])

            # trend (linear regression slope)
            if series.size >= 3: # Need at least 3 points for stable trend
                x = np.arange(series.size)
                coeffs = np.polyfit(x, series, 1)
                features[f"{s_name}_trend"] = float(coeffs[0])
            else:
                features[f"{s_name}_trend"] = 0.0

        # Health index upgrades: Use EMA values for health if available
        current_ema_sum = sum(features[f"{s}_ema"] for s in self.SENSOR_COLS)
        base_sum = float(engine.base_sensors.sum())
        if base_sum > 0:
            health_index = current_ema_sum / base_sum
        else:
            health_index = 1.0
        features["health_index"] = float(np.clip(health_index, 0.0, 1.5))

        # Life ratio: cycle relative to design life
        life_ratio = engine.cycle / max(engine.design_life, 1)
        features["life_ratio"] = float(np.clip(life_ratio, 0.0, 2.0))
        
        # Interactions
        features["health_x_cycle"] = features["health_index"] * float(engine.cycle)
        features["health_x_liferatio"] = features["health_index"] * features["life_ratio"]

        # Fill NaNs from pandas stats operations if any
        for k, v in features.items():
            if np.isnan(v):
                features[k] = 0.0

        return features

    def build_feature_row(
        self,
        engine: EngineState,
        cycle: int,
        sensors: np.ndarray,
        op_settings: np.ndarray,
    ) -> Dict[str, float]:
        row: Dict[str, float] = {
            "engine_id": float(engine.engine_id),
            "cycle": float(cycle),
            # Expose design life for Weibull risk calculation
            "design_life": float(engine.design_life),
        }

        # raw sensor and setting values
        for i, name in enumerate(self.SENSOR_COLS):
            row[name] = float(sensors[i])
        for i, name in enumerate(self.SETTING_COLS):
            row[name] = float(op_settings[i])

        row.update(self._compute_sensor_features(engine, sensors))
        return row


class ModelPredictor:
    """
    Wraps XGBRegressor for RUL prediction and derives a simple failure probability.
    """

    def __init__(self, model_path: str, expected_features: List[str] | None = None) -> None:
        """
        Load an XGBoost model saved either as:
        - native XGBoost JSON/binary (for XGBRegressor)  -> use load_model
        - Python pickle / joblib (.pkl, .pickle, .joblib) -> use joblib.load
        """
        self.rng = np.random.default_rng(seed=42)
        model_path_lower = model_path.lower()
        if model_path_lower.endswith((".pkl", ".pickle", ".joblib")):
            # sklearn-style pickled model
            self.model = joblib.load(model_path)
        else:
            # native XGBoost model file
            self.model = XGBRegressor()
            self.model.load_model(model_path)

        # Determine feature order
        booster_feature_names: List[str] = []
        try:
            booster = self.model.get_booster()
            booster_feature_names = booster.feature_names or []
        except Exception:
            booster_feature_names = []

        if expected_features is not None:
            self.feature_order = expected_features
        elif booster_feature_names:
            self.feature_order = list(booster_feature_names)
        else:
            raise ValueError(
                "Could not infer feature names from model. "
                "Please pass expected_features that matches training."
            )

    def _align_features(self, df: pd.DataFrame) -> pd.DataFrame:
        aligned = df.reindex(columns=self.feature_order, fill_value=0.0)
        return aligned.astype(float)

    def predict_batch(self, features: List[Dict[str, float]]) -> Tuple[np.ndarray, np.ndarray]:
        df = pd.DataFrame(features)
        X = self._align_features(df)

        rul_pred = self.model.predict(X)

        # Absolute risk scale: failure_prob = 1 - RUL / critical_RUL (clip to [0,1]).
        # Risk depends on distance to failure in real units, not relative to batch.
        denom = max(CRITICAL_RUL_FOR_RISK, 1e-6)
        # Weibull‑based risk (cumulative distribution function)
        cycle_array = np.array([int(f.get('cycle', 0)) for f in features])
        design_life_arr = np.array([float(f.get('design_life', 3000)) for f in features])
        weibull_risk = 1 - np.exp(- (cycle_array / (design_life_arr * WEIBULL_SCALE)) ** WEIBULL_BETA)
        # Blend linear and Weibull risks equally (adjust weighting if desired)
        linear_risk = 1 - rul_pred / denom
        failure_prob = 0.5 * weibull_risk + 0.5 * linear_risk
        # Add a tiny random jitter (±5%) to spread risk across engines
        jitter = self.rng.normal(loc=0.0, scale=0.05, size=failure_prob.shape)
        # Apply jitter to avoid exact ties
        failure_prob = np.clip(failure_prob + jitter, 0.0, 1.0)

        return rul_pred, failure_prob


class MongoSink:
    def __init__(self, uri: str, db_name: str, collection_name: str = "live_predictions") -> None:
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.history_collection = self.db["maintenance_log"]

    def log_failure(self, engine_id: int, cycle: int, final_rul: float) -> None:
        """Logs a permanent entry when an engine requires maintenance/replacement."""
        self.history_collection.insert_one({
            "timestamp": time.time(),
            "engine_id": engine_id,
            "cycle": cycle,
            "final_rul": final_rul,
            "action": "AUTO_REPLACEMENT",
            "reason": "CRITICAL_RUL_BREACH"
        })

    def write_batch(
        self,
        batch_features: List[Dict[str, float]],
        rul: np.ndarray,
        failure_prob: np.ndarray,
    ) -> None:
        ts = time.time()
        docs = []
        for feat, r, p in zip(batch_features, rul, failure_prob):
            docs.append(
                {
                    "_id": str(uuid.uuid4()),
                    "timestamp": ts,
                    "engine_id": int(feat.get("engine_id", -1)),
                    "cycle": int(feat.get("cycle", -1)),
                    "predicted_rul": float(r),
                    "failure_probability": float(p),
                    "features": feat,
                }
            )
        if docs:
            self.collection.insert_many(docs, ordered=False)


class TelemetrySimulator:
    def __init__(
        self,
        num_engines: int,
        model_path: str,
        mongo_uri: str,
        mongo_db: str,
        expected_features: List[str] | None = None,
        batch_interval_seconds: float = BATCH_INTERVAL_SECONDS,
    ) -> None:
        self.rng = np.random.default_rng(seed=42)
        self.engines = [
            self._create_engine(engine_id=i) for i in range(1, num_engines + 1)
        ]
        self.fe = FeatureEngineer()
        self.predictor = ModelPredictor(model_path=model_path, expected_features=expected_features)
        self.sink = MongoSink(uri=mongo_uri, db_name=mongo_db)
        self.batch_interval_seconds = batch_interval_seconds

    def _create_engine(self, engine_id: int) -> EngineState:
        eng = EngineState(engine_id=engine_id)
        eng.initialize_random(self.rng)
        # Stagger fleet "age" so some engines are already late-life.
        # This better matches real deployments where assets are not all brand new at t=0.
        # We back-calculate by setting the cycle so that after warm-up we land on target_cycle.
        target_cycle = int(self.rng.integers(0, max(eng.design_life, 1)))
        eng.cycle = max(0, target_cycle - ROLLING_WINDOW)

        # Warm‑up history to populate rolling features at the target cycle.
        for _ in range(ROLLING_WINDOW):
            eng.next_reading(self.rng)
        return eng

    def _generate_batch(self) -> List[Dict[str, float]]:
        batch_rows: List[Dict[str, float]] = []
        for eng in self.engines:
            cycle, sensors, op_settings = eng.next_reading(self.rng)
            row = self.fe.build_feature_row(eng, cycle, sensors, op_settings)
            batch_rows.append(row)
        return batch_rows

    def run_forever(self) -> None:
        print("Starting real-time engine telemetry simulation...")
        batch_idx = 0
        # Keep track of which engines are currently under a burst
        burst_engine_ids: set[int] = set()
        while True:
            batch_idx += 1
            start = time.time()

            # ----- Stress‑burst handling -----
            if batch_idx % BURST_INTERVAL == 0:
                # Determine how many engines to affect
                n_burst = max(1, int(len(self.engines) * BURST_PERCENTAGE))
                burst_engine_ids = set(self.rng.choice([e.engine_id for e in self.engines], size=n_burst, replace=False))
                for eng in self.engines:
                    if eng.engine_id in burst_engine_ids:
                        eng.burst_multiplier = BURST_MULTIPLIER

            features = self._generate_batch()
            rul_pred, failure_prob = self.predictor.predict_batch(features)

            # Failure & replacement: RUL below absolute threshold → log and replace.
            failed_mask = rul_pred < FAILURE_RUL_THRESHOLD
            failed_indices = np.where(failed_mask)[0]
            num_failed = int(len(failed_indices))

            for idx in failed_indices:
                engine_id = self.engines[idx].engine_id
                cycle = int(features[idx].get("cycle", -1))
                rul = float(rul_pred[idx])
                print(f"  Failure: engine_id={engine_id} cycle={cycle} predicted_rul={rul:.1f} → replacing")
                self.sink.log_failure(engine_id, cycle, rul)
                self.engines[idx] = self._create_engine(engine_id=engine_id)

            self.sink.write_batch(features, rul_pred, failure_prob)

            # Risk bands: warning (WARNING_THRESHOLD, HIGH_RISK_THRESHOLD], critical > HIGH_RISK_THRESHOLD
            critical = int((failure_prob > HIGH_RISK_THRESHOLD).sum())
            warning = int(((failure_prob > HIGH_WARNING_THRESHOLD) & (failure_prob <= HIGH_RISK_THRESHOLD)).sum())
            mean_rul = float(rul_pred.mean())
            min_rul = float(rul_pred.min())
            max_rul = float(rul_pred.max())
            mean_fail = float(failure_prob.mean())

            print(
                f"[Batch {batch_idx}] engines={len(self.engines)} "
                f"mean_RUL={mean_rul:.2f} min_RUL={min_rul:.2f} max_RUL={max_rul:.2f} "
                f"mean_failure_prob={mean_fail:.3f} critical={critical} warning={warning} "
                f"failed_and_replaced={num_failed}"
            )

            elapsed = time.time() - start
            sleep_time = max(0.0, self.batch_interval_seconds - elapsed)
            time.sleep(sleep_time)


def load_expected_features_from_env() -> List[str] | None:
    """
    Optionally provide EXACT feature order via environment variable
    EXPECTED_FEATURES as a comma‑separated list.
    This should match the features used during model training.
    """
    raw = os.getenv("EXPECTED_FEATURES")
    if not raw:
        return None
    return [f.strip() for f in raw.split(",") if f.strip()]


def main() -> None:
    model_path = os.getenv("XGB_MODEL_PATH", "xgb_rul_model.json")
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongo_db = os.getenv("MONGODB_DB", "engine_telemetry")

    expected_features = load_expected_features_from_env()

    sim = TelemetrySimulator(
        num_engines=NUM_ENGINES,
        model_path=model_path,
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        expected_features=expected_features,
        batch_interval_seconds=BATCH_INTERVAL_SECONDS,
    )
    sim.run_forever()


if __name__ == "__main__":
    main()

