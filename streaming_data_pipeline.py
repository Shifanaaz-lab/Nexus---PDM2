"""
Production-Ready Streaming Data Pipeline for Predictive Maintenance
Handles real-time telemetry processing with proper feature engineering and model inference
"""

import os
import time
import uuid
import json
import logging
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

import numpy as np
import pandas as pd
from pymongo import MongoClient
from xgboost import XGBRegressor
import joblib

from enhanced_feature_engineering import EnhancedFeatureEngineer
from optimized_model_training import OptimizedModelTrainer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TelemetryData:
    """Structure for incoming telemetry data"""
    engine_id: int
    cycle: int
    timestamp: float
    sensors: np.ndarray
    op_settings: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Structure for prediction results"""
    engine_id: int
    cycle: int
    timestamp: float
    predicted_rul: float
    failure_probability: float
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    features: Dict[str, float] = field(default_factory=dict)
    model_version: str = "unknown"


class EngineStateManager:
    """
    Manages state for multiple engines in a streaming context.
    Ensures proper temporal ordering and prevents data leakage.
    """
    
    def __init__(self, max_history_length: int = 100):
        self.engines: Dict[int, Dict] = {}
        self.max_history_length = max_history_length
        self.lock = threading.Lock()
    
    def update_engine_state(
        self, 
        engine_id: int, 
        cycle: int, 
        sensors: np.ndarray, 
        op_settings: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Update engine state with new telemetry data.
        """
        with self.lock:
            if engine_id not in self.engines:
                self.engines[engine_id] = {
                    'engine_id': engine_id,
                    'cycle': 0,
                    'history': deque(maxlen=self.max_history_length),
                    'design_life': metadata.get('design_life', 3000) if metadata else 3000,
                    'first_seen': time.time(),
                    'last_update': time.time(),
                    'metadata': metadata or {}
                }
            
            engine_state = self.engines[engine_id]
            
            # Validate temporal ordering
            if cycle <= engine_state['cycle']:
                logger.warning(f"Out-of-order data for engine {engine_id}: cycle {cycle} <= {engine_state['cycle']}")
                return engine_state
            
            # Update state
            engine_state['cycle'] = cycle
            engine_state['history'].append(sensors.copy())
            engine_state['last_update'] = time.time()
            
            return engine_state
    
    def get_engine_state(self, engine_id: int) -> Optional[Dict]:
        """Get current state of an engine."""
        with self.lock:
            return self.engines.get(engine_id)
    
    def remove_engine(self, engine_id: int) -> bool:
        """Remove engine from state management."""
        with self.lock:
            if engine_id in self.engines:
                del self.engines[engine_id]
                return True
            return False
    
    def get_all_engine_ids(self) -> List[int]:
        """Get list of all active engine IDs."""
        with self.lock:
            return list(self.engines.keys())
    
    def cleanup_stale_engines(self, max_idle_time: float = 3600.0) -> List[int]:
        """Remove engines that haven't been updated recently."""
        current_time = time.time()
        stale_engines = []
        
        with self.lock:
            for engine_id, state in self.engines.items():
                if current_time - state['last_update'] > max_idle_time:
                    stale_engines.append(engine_id)
            
            for engine_id in stale_engines:
                del self.engines[engine_id]
        
        return stale_engines


class StreamingFeatureProcessor:
    """
    Processes streaming telemetry data and generates features in real-time.
    Optimized for low-latency inference.
    """
    
    def __init__(self, feature_engineer: EnhancedFeatureEngineer):
        self.feature_engineer = feature_engineer
        self.feature_cache: Dict[int, Dict] = {}
        self.cache_lock = threading.Lock()
    
    def process_telemetry(
        self, 
        telemetry: TelemetryData, 
        engine_state: Dict
    ) -> PredictionResult:
        """
        Process single telemetry reading and return prediction-ready features.
        """
        # Build feature row
        features = self.feature_engineer.build_feature_row(
            engine_state=engine_state,
            cycle=telemetry.cycle,
            sensors=telemetry.sensors,
            op_settings=telemetry.op_settings,
            history=np.array(engine_state['history']) if engine_state['history'] else None
        )
        
        # Cache features for potential debugging
        with self.cache_lock:
            self.feature_cache[telemetry.engine_id] = {
                'features': features,
                'timestamp': telemetry.timestamp,
                'cycle': telemetry.cycle
            }
        
        return features
    
    def get_cached_features(self, engine_id: int) -> Optional[Dict]:
        """Get cached features for an engine."""
        with self.cache_lock:
            return self.feature_cache.get(engine_id)
    
    def clear_cache(self, engine_id: Optional[int] = None):
        """Clear feature cache."""
        with self.cache_lock:
            if engine_id:
                self.feature_cache.pop(engine_id, None)
            else:
                self.feature_cache.clear()


class ModelInferenceEngine:
    """
    Handles model inference with ensemble support and uncertainty quantification.
    """
    
    def __init__(
        self, 
        model_paths: List[str],
        feature_engineer_path: str,
        expected_features: List[str]
    ):
        self.models = []
        self.feature_engineer = joblib.load(feature_engineer_path)
        self.expected_features = expected_features
        self.model_version = "v1.0"
        
        # Load ensemble models
        for model_path in model_paths:
            model = XGBRegressor()
            model.load_model(model_path)
            self.models.append(model)
        
        logger.info(f"Loaded {len(self.models)} models for inference")
    
    def predict(
        self, 
        features: Dict[str, float],
        use_ensemble: bool = True
    ) -> Tuple[float, float, Tuple[float, float]]:
        """
        Make RUL prediction with uncertainty bounds.
        
        Returns:
            Tuple of (predicted_rul, failure_probability, confidence_interval)
        """
        # Prepare features
        feature_df = pd.DataFrame([features])
        
        # Align with expected features
        aligned_features = feature_df.reindex(columns=self.expected_features, fill_value=0.0)
        
        if use_ensemble and len(self.models) > 1:
            # Ensemble prediction
            predictions = []
            for model in self.models:
                pred = model.predict(aligned_features)[0]
                predictions.append(pred)
            
            predictions = np.array(predictions)
            mean_pred = np.mean(predictions)
            std_pred = np.std(predictions)
            
            # Confidence interval (95%)
            confidence_interval = (
                max(0.0, mean_pred - 1.96 * std_pred),
                mean_pred + 1.96 * std_pred
            )
        else:
            # Single model prediction
            mean_pred = self.models[0].predict(aligned_features)[0]
            confidence_interval = (mean_pred, mean_pred)
        
        # Calculate failure probability
        critical_rul = 500.0  # Configurable threshold
        failure_prob = np.clip(1.0 - mean_pred / critical_rul, 0.0, 1.0)
        
        return float(mean_pred), float(failure_prob), confidence_interval
    
    def predict_batch(
        self, 
        features_list: List[Dict[str, float]],
        use_ensemble: bool = True
    ) -> List[PredictionResult]:
        """
        Batch prediction for multiple engines.
        """
        results = []
        
        for features in features_list:
            engine_id = int(features.get('engine_id', 0))
            cycle = int(features.get('cycle', 0))
            timestamp = time.time()
            
            predicted_rul, failure_prob, confidence_interval = self.predict(
                features, use_ensemble
            )
            
            result = PredictionResult(
                engine_id=engine_id,
                cycle=cycle,
                timestamp=timestamp,
                predicted_rul=predicted_rul,
                failure_probability=failure_prob,
                confidence_interval=confidence_interval,
                features=features,
                model_version=self.model_version
            )
            
            results.append(result)
        
        return results


class DataSink:
    """
    Handles data persistence and alerting.
    """
    
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str = "predictions"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.alerts_collection = self.db["alerts"]
        self.maintenance_log = self.db["maintenance_log"]
    
    def store_predictions(self, results: List[PredictionResult]):
        """Store prediction results in MongoDB."""
        docs = []
        for result in results:
            doc = {
                "_id": str(uuid.uuid4()),
                "engine_id": result.engine_id,
                "cycle": result.cycle,
                "timestamp": result.timestamp,
                "predicted_rul": result.predicted_rul,
                "failure_probability": result.failure_probability,
                "confidence_interval": result.confidence_interval,
                "features": result.features,
                "model_version": result.model_version
            }
            docs.append(doc)
        
        if docs:
            self.collection.insert_many(docs, ordered=False)
            logger.info(f"Stored {len(docs)} predictions")
    
    def check_and_create_alerts(self, results: List[PredictionResult]):
        """Check for critical conditions and create alerts."""
        alerts = []
        
        for result in results:
            # Critical RUL alert
            if result.predicted_rul < 100:
                alert = {
                    "_id": str(uuid.uuid4()),
                    "engine_id": result.engine_id,
                    "cycle": result.cycle,
                    "timestamp": result.timestamp,
                    "alert_type": "CRITICAL_RUL",
                    "severity": "HIGH",
                    "message": f"Engine {result.engine_id} predicted RUL: {result.predicted_rul:.1f}",
                    "predicted_rul": result.predicted_rul,
                    "failure_probability": result.failure_probability
                }
                alerts.append(alert)
            
            # High failure probability alert
            elif result.failure_probability > 0.8:
                alert = {
                    "_id": str(uuid.uuid4()),
                    "engine_id": result.engine_id,
                    "cycle": result.cycle,
                    "timestamp": result.timestamp,
                    "alert_type": "HIGH_FAILURE_RISK",
                    "severity": "MEDIUM",
                    "message": f"Engine {result.engine_id} failure probability: {result.failure_probability:.3f}",
                    "predicted_rul": result.predicted_rul,
                    "failure_probability": result.failure_probability
                }
                alerts.append(alert)
        
        if alerts:
            self.alerts_collection.insert_many(alerts, ordered=False)
            logger.warning(f"Created {len(alerts)} alerts")
    
    def log_maintenance_action(
        self, 
        engine_id: int, 
        cycle: int, 
        action: str, 
        reason: str,
        final_rul: float
    ):
        """Log maintenance actions."""
        doc = {
            "_id": str(uuid.uuid4()),
            "engine_id": engine_id,
            "cycle": cycle,
            "timestamp": time.time(),
            "action": action,
            "reason": reason,
            "final_rul": final_rul
        }
        
        self.maintenance_log.insert_one(doc)
        logger.info(f"Logged maintenance action for engine {engine_id}: {action}")


class StreamingPipeline:
    """
    Main streaming pipeline that orchestrates all components.
    """
    
    def __init__(
        self,
        model_paths: List[str],
        feature_engineer_path: str,
        expected_features: List[str],
        mongo_uri: str = "mongodb://localhost:27017/",
        mongo_db: str = "predictive_maintenance",
        batch_size: int = 100,
        processing_interval: float = 1.0
    ):
        self.state_manager = EngineStateManager()
        self.feature_processor = StreamingFeatureProcessor(
            joblib.load(feature_engineer_path)
        )
        self.inference_engine = ModelInferenceEngine(
            model_paths, feature_engineer_path, expected_features
        )
        self.data_sink = DataSink(mongo_uri, mongo_db)
        
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        self.running = False
        
        # Thread-safe queue for incoming telemetry
        self.telemetry_queue = queue.Queue(maxsize=10000)
        
        # Metrics
        self.metrics = {
            'processed_samples': 0,
            'failed_samples': 0,
            'alerts_created': 0,
            'maintenance_actions': 0
        }
    
    def add_telemetry_data(self, telemetry: TelemetryData):
        """Add telemetry data to processing queue."""
        try:
            self.telemetry_queue.put_nowait(telemetry)
        except queue.Full:
            logger.error("Telemetry queue is full, dropping data")
            self.metrics['failed_samples'] += 1
    
    def process_batch(self) -> List[PredictionResult]:
        """Process a batch of telemetry data."""
        batch_data = []
        results = []
        
        # Collect batch
        for _ in range(self.batch_size):
            try:
                telemetry = self.telemetry_queue.get_nowait()
                batch_data.append(telemetry)
            except queue.Empty:
                break
        
        if not batch_data:
            return results
        
        # Process each telemetry reading
        for telemetry in batch_data:
            try:
                # Update engine state
                engine_state = self.state_manager.update_engine_state(
                    telemetry.engine_id,
                    telemetry.cycle,
                    telemetry.sensors,
                    telemetry.op_settings,
                    telemetry.metadata
                )
                
                # Process features
                features = self.feature_processor.process_telemetry(telemetry, engine_state)
                
                # Make prediction
                prediction_results = self.inference_engine.predict_batch([features])
                results.extend(prediction_results)
                
                self.metrics['processed_samples'] += 1
                
            except Exception as e:
                logger.error(f"Error processing telemetry for engine {telemetry.engine_id}: {e}")
                self.metrics['failed_samples'] += 1
        
        # Store results and check for alerts
        if results:
            self.data_sink.store_predictions(results)
            self.data_sink.check_and_create_alerts(results)
        
        return results
    
    def run_forever(self):
        """Run the streaming pipeline continuously."""
        self.running = True
        logger.info("Starting streaming pipeline...")
        
        while self.running:
            start_time = time.time()
            
            try:
                # Process batch
                results = self.process_batch()
                
                # Cleanup stale engines
                stale_engines = self.state_manager.cleanup_stale_engines()
                if stale_engines:
                    logger.info(f"Cleaned up {len(stale_engines)} stale engines")
                
                # Log metrics
                if results:
                    logger.info(
                        f"Processed {len(results)} predictions. "
                        f"Total processed: {self.metrics['processed_samples']}, "
                        f"Failed: {self.metrics['failed_samples']}"
                    )
                
                # Sleep for remaining time
                elapsed = time.time() - start_time
                sleep_time = max(0.0, self.processing_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in streaming pipeline: {e}")
                time.sleep(self.processing_interval)
    
    def stop(self):
        """Stop the streaming pipeline."""
        self.running = False
        logger.info("Stopping streaming pipeline...")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics."""
        return {
            **self.metrics,
            'active_engines': len(self.state_manager.get_all_engine_ids()),
            'queue_size': self.telemetry_queue.qsize()
        }


def create_sample_telemetry(engine_id: int, cycle: int) -> TelemetryData:
    """Create sample telemetry data for testing."""
    rng = np.random.default_rng(engine_id + cycle)
    
    sensors = rng.uniform([20.0, 600.0, 900.0], [50.0, 800.0, 1100.0])
    op_settings = np.array([
        rng.uniform(0.0, 1.0),
        rng.uniform(20.0, 40.0),
        rng.uniform(900.0, 1100.0)
    ])
    
    return TelemetryData(
        engine_id=engine_id,
        cycle=cycle,
        timestamp=time.time(),
        sensors=sensors,
        op_settings=op_settings,
        metadata={'design_life': 3000}
    )


def main():
    """Example usage of the streaming pipeline."""
    
    # Model paths (adjust as needed)
    model_paths = [
        "optimized_xgb_rul_model.json",
        "optimized_xgb_rul_model_ensemble_1.json",
        "optimized_xgb_rul_model_ensemble_2.json"
    ]
    
    feature_engineer_path = "optimized_xgb_rul_model_feature_engineer.pkl"
    
    # Load expected features from metadata
    with open("optimized_xgb_rul_model_metadata.json", 'r') as f:
        metadata = json.load(f)
    expected_features = metadata['feature_names']
    
    # Create and start pipeline
    pipeline = StreamingPipeline(
        model_paths=model_paths,
        feature_engineer_path=feature_engineer_path,
        expected_features=expected_features,
        batch_size=50,
        processing_interval=2.0
    )
    
    # Start pipeline in background thread
    pipeline_thread = threading.Thread(target=pipeline.run_forever, daemon=True)
    pipeline_thread.start()
    
    # Simulate incoming telemetry
    try:
        for cycle in range(1, 100):
            for engine_id in range(1, 6):  # 5 engines
                telemetry = create_sample_telemetry(engine_id, cycle)
                pipeline.add_telemetry_data(telemetry)
            
            time.sleep(0.1)  # Simulate real-time data arrival
            
            if cycle % 20 == 0:
                metrics = pipeline.get_metrics()
                print(f"Metrics: {metrics}")
    
    except KeyboardInterrupt:
        print("Stopping pipeline...")
        pipeline.stop()
    
    return pipeline


if __name__ == "__main__":
    main()
