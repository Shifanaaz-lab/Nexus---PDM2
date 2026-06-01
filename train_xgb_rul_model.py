import os
import json
from typing import Tuple

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from real_time_engine_telemetry import (
    EngineState,
    FeatureEngineer,
    ROLLING_WINDOW,
    MAX_RUL_CAP,
)


NUM_TRAIN_ENGINES = 100
RUL_HORIZON_MULTIPLIER = 1.2  # simulate beyond nominal design life


def generate_training_data(
    num_engines: int = NUM_TRAIN_ENGINES,
    random_state: int = 0,
) -> Tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(random_state)
    fe = FeatureEngineer()

    rows = []
    labels = []

    for engine_id in range(1, num_engines + 1):
        eng = EngineState(engine_id=engine_id)
        eng.initialize_random(rng)

        # Warm‑up history to be consistent with the live simulator
        for _ in range(ROLLING_WINDOW):
            _, sensors, op_settings = eng.next_reading(rng)

        max_cycles = int(eng.design_life * RUL_HORIZON_MULTIPLIER)

        for _ in range(max_cycles):
            cycle, sensors, op_settings = eng.next_reading(rng)
            feat = fe.build_feature_row(eng, cycle, sensors, op_settings)

            # Piecewise RUL label: capped at MAX_RUL_CAP for healthy engines
            # Industry standard for NASA C-MAPPS modeling.
            raw_rul = eng.design_life - cycle
            rul = min(float(raw_rul), float(MAX_RUL_CAP))
            rul = max(rul, 0.0)

            rows.append(feat)
            labels.append(rul)

    X = pd.DataFrame(rows)
    y = np.asarray(labels, dtype=float)
    return X, y


def train_and_save_model(
    output_prefix: str = "xgb_rul_model",
) -> None:
    print("Generating synthetic training data...")
    X, y = generate_training_data()

    print(f"Training data: {X.shape[0]:,} rows, {X.shape[1]} features")

    # Load best params from tuning
    best_params = {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
    }
    if os.path.exists("best_xgb_params.json"):
        with open("best_xgb_params.json", "r") as f:
            best_params.update(json.load(f))
        print("  Using best parameters from tuning script.")

    # 1. Train Primary Accuracy Model (Standard Regression)
    print("Training primary XGBoost model for accuracy (reg:squarederror)...")
    accuracy_model = XGBRegressor(
        **best_params,
        objective="reg:squarederror",
        tree_method="hist",
        n_jobs=-1
    )
    accuracy_model.fit(X, y)
    accuracy_model.save_model(f"{output_prefix}.json")
    print(f"  Saved primary model to {os.path.abspath(output_prefix + '.json')}")

    # 2. Train Quantile Models (Uncertainty Bounds)
    quantiles = [0.1, 0.9] # lower and upper bounds
    names = ["lower", "upper"]

    for q, name in zip(quantiles, names):
        print(f"Training XGBoost model for quantile {q} ({name})...")
        
        model = XGBRegressor(
            **best_params,
            objective="reg:quantileerror",
            quantile_alpha=q,
            tree_method="hist",
            n_jobs=-1
        )

        model.fit(X, y)
        
        output_path = f"{output_prefix}_{name}.json"
        model.save_model(output_path)
        print(f"  Saved {name} model to {os.path.abspath(output_path)}")

    print("\nFeature order used during training:")
    print(",".join(X.columns))


if __name__ == "__main__":
    train_and_save_model()


