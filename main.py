"""
Main Application Entry Point
Production-ready predictive maintenance system with enhanced ML pipeline
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from deployment_config import ConfigManager
from optimized_model_training import OptimizedModelTrainer
from model_evaluation_monitoring import ModelEvaluator, RealTimeMonitor, PerformanceVisualizer
from streaming_data_pipeline import StreamingPipeline, TelemetryData


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/predictive_maintenance.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)


def train_models(config_manager: ConfigManager, args):
    """Train and evaluate models"""
    logger.info("Starting model training...")
    
    # Initialize trainer
    trainer = OptimizedModelTrainer(
        n_trials=args.trials if hasattr(args, 'trials') else 50,
        cv_folds=5,
        use_optuna=not args.no_optuna if hasattr(args, 'no_optuna') else True
    )
    
    # Generate training data
    num_engines = args.engines if hasattr(args, 'engines') else 100
    X, y = trainer.generate_training_data(num_engines=num_engines)
    
    # Optimize hyperparameters
    best_params = trainer.optimize_hyperparameters(X, y)
    
    # Train ensemble models
    models = trainer.train_ensemble_models(X, y, n_models=3)
    
    # Evaluate models
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate_model_comprehensive(
        models[0], X, y, trainer.feature_engineer.get_feature_names()
    )
    
    # Print evaluation report
    report = evaluator.generate_evaluation_report(metrics)
    print(report)
    
    # Save models
    trainer.save_models(models, "optimized_xgb_rul_model")
    
    # Create visualizations
    visualizer = PerformanceVisualizer()
    y_pred = models[0].predict(X)
    visualizer.plot_prediction_vs_actual(y, y_pred)
    visualizer.plot_residuals(y, y_pred)
    visualizer.plot_feature_importance(models[0], trainer.feature_engineer.get_feature_names())
    
    logger.info("Model training completed successfully")
    return trainer, models, metrics


def start_streaming_pipeline(config_manager: ConfigManager):
    """Start the streaming pipeline"""
    logger.info("Starting streaming pipeline...")
    
    # Initialize pipeline
    pipeline = StreamingPipeline(
        model_paths=config_manager.config.model.model_paths,
        feature_engineer_path=config_manager.config.model.feature_engineer_path,
        expected_features=[],  # Will be loaded from metadata
        mongo_uri=config_manager.config.database.mongodb_uri,
        mongo_db=config_manager.config.database.database_name,
        batch_size=config_manager.config.streaming.batch_size,
        processing_interval=config_manager.config.streaming.processing_interval_seconds
    )
    
    # Start pipeline in background
    import threading
    pipeline_thread = threading.Thread(target=pipeline.run_forever, daemon=True)
    pipeline_thread.start()
    
    logger.info("Streaming pipeline started")
    return pipeline


def run_evaluation(config_manager: ConfigManager):
    """Run model evaluation"""
    logger.info("Running model evaluation...")
    
    # Load model and metadata
    from xgboost import XGBRegressor
    import joblib
    import json
    
    try:
        model = XGBRegressor()
        model.load_model(config_manager.config.model.model_paths[0])
        
        with open(config_manager.config.model.metadata_path, 'r') as f:
            metadata = json.load(f)
        
        feature_engineer = joblib.load(config_manager.config.model.feature_engineer_path)
        
        # Generate test data
        trainer = OptimizedModelTrainer()
        X_test, y_test = trainer.generate_training_data(num_engines=50)
        
        # Evaluate model
        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate_model_comprehensive(
            model, X_test, y_test, metadata['feature_names']
        )
        
        # Generate report
        report = evaluator.generate_evaluation_report(metrics)
        print(report)
        
        # Create visualizations
        visualizer = PerformanceVisualizer()
        y_pred = model.predict(X_test)
        visualizer.plot_prediction_vs_actual(y_test, y_pred)
        visualizer.plot_residuals(y_test, y_pred)
        visualizer.plot_feature_importance(model, metadata['feature_names'])
        
        logger.info("Evaluation completed")
        return metrics
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return None


def run_simulation(config_manager: ConfigManager, duration_minutes: int = 10):
    """Run simulation with streaming pipeline"""
    logger.info(f"Running simulation for {duration_minutes} minutes...")
    
    # Start streaming pipeline
    pipeline = start_streaming_pipeline(config_manager)
    
    # Initialize real-time monitor
    monitor = RealTimeMonitor()
    
    # Simulate telemetry data
    import numpy as np
    from streaming_data_pipeline import create_sample_telemetry
    
    end_time = time.time() + (duration_minutes * 60)
    cycle_counter = 1
    
    try:
        while time.time() < end_time:
            # Generate telemetry for multiple engines
            for engine_id in range(1, 6):  # 5 engines
                telemetry = create_sample_telemetry(engine_id, cycle_counter)
                pipeline.add_telemetry_data(telemetry)
                
                # Add to monitor for tracking
                if hasattr(pipeline, 'inference_engine'):
                    features = pipeline.feature_processor.process_telemetry(
                        telemetry, 
                        pipeline.state_manager.get_engine_state(engine_id) or {}
                    )
                    
                    # Simple prediction for monitoring
                    predicted_rul = np.random.normal(100, 20)  # Simulated prediction
                    actual_rul = max(0, 300 - cycle_counter)  # Simulated actual
                    
                    monitor.add_prediction(
                        engine_id=engine_id,
                        features=features,
                        predicted_rul=predicted_rul,
                        actual_rul=actual_rul
                    )
            
            cycle_counter += 1
            
            # Print metrics every 20 cycles
            if cycle_counter % 20 == 0:
                pipeline_metrics = pipeline.get_metrics()
                monitoring_summary = monitor.get_monitoring_summary()
                
                print(f"Cycle {cycle_counter}")
                print(f"Pipeline: {pipeline_metrics}")
                print(f"Monitoring: {monitoring_summary}")
                print("-" * 50)
            
            time.sleep(0.1)  # Simulate real-time data arrival
    
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    
    finally:
        pipeline.stop()
        logger.info("Simulation completed")


def create_api_server(config_manager: ConfigManager):
    """Create FastAPI server for the predictive maintenance system"""
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Dict, Any
    import uvicorn
    
    app = FastAPI(
        title="Predictive Maintenance API",
        description="Real-time predictive maintenance system",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize pipeline
    pipeline = None
    
    class TelemetryRequest(BaseModel):
        engine_id: int
        cycle: int
        sensors: List[float]
        op_settings: List[float]
        metadata: Dict[str, Any] = {}
    
    class PredictionResponse(BaseModel):
        engine_id: int
        cycle: int
        predicted_rul: float
        failure_probability: float
        confidence_interval: List[float]
        timestamp: float
    
    @app.on_event("startup")
    async def startup_event():
        nonlocal pipeline
        try:
            pipeline = start_streaming_pipeline(config_manager)
            logger.info("API server started successfully")
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
    @app.post("/predict", response_model=PredictionResponse)
    async def predict_rul(
        request: TelemetryRequest,
        background_tasks: BackgroundTasks
    ):
        """Predict RUL for a single engine reading"""
        if not pipeline:
            raise HTTPException(status_code=503, detail="Pipeline not available")
        
        try:
            # Create telemetry data
            telemetry = TelemetryData(
                engine_id=request.engine_id,
                cycle=request.cycle,
                timestamp=time.time(),
                sensors=np.array(request.sensors),
                op_settings=np.array(request.op_settings),
                metadata=request.metadata
            )
            
            # Add to pipeline for processing
            pipeline.add_telemetry_data(telemetry)
            
            # Get immediate prediction (simplified)
            engine_state = pipeline.state_manager.get_engine_state(request.engine_id) or {
                'engine_id': request.engine_id,
                'history': [],
                'design_life': request.metadata.get('design_life', 3000)
            }
            
            features = pipeline.feature_processor.process_telemetry(telemetry, engine_state)
            prediction_results = pipeline.inference_engine.predict_batch([features])
            
            if prediction_results:
                result = prediction_results[0]
                return PredictionResponse(
                    engine_id=result.engine_id,
                    cycle=result.cycle,
                    predicted_rul=result.predicted_rul,
                    failure_probability=result.failure_probability,
                    confidence_interval=list(result.confidence_interval),
                    timestamp=result.timestamp
                )
            else:
                raise HTTPException(status_code=500, detail="Prediction failed")
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/metrics")
    async def get_metrics():
        """Get system metrics"""
        if not pipeline:
            raise HTTPException(status_code=503, detail="Pipeline not available")
        
        return pipeline.get_metrics()
    
    @app.get("/alerts")
    async def get_alerts():
        """Get recent alerts"""
        if not pipeline:
            raise HTTPException(status_code=503, detail="Pipeline not available")
        
        # This would need to be implemented based on your alert storage
        return {"alerts": [], "count": 0}
    
    return app


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Predictive Maintenance System")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file path")
    parser.add_argument("--mode", type=str, choices=["train", "evaluate", "stream", "simulate", "api"], 
                       default="api", help="Operation mode")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")
    
    # Training arguments
    parser.add_argument("--engines", type=int, default=100, help="Number of engines for training")
    parser.add_argument("--trials", type=int, default=50, help="Number of optimization trials")
    parser.add_argument("--no-optuna", action="store_true", help="Disable hyperparameter optimization")
    
    # Simulation arguments
    parser.add_argument("--duration", type=int, default=10, help="Simulation duration in minutes")
    
    # API arguments
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config_manager = ConfigManager(args.config)
        logger.info(f"Configuration loaded from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Run based on mode
    try:
        if args.mode == "train":
            trainer, models, metrics = train_models(config_manager, args)
            
        elif args.mode == "evaluate":
            metrics = run_evaluation(config_manager)
            
        elif args.mode == "stream":
            pipeline = start_streaming_pipeline(config_manager)
            logger.info("Streaming pipeline running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping pipeline...")
                pipeline.stop()
                
        elif args.mode == "simulate":
            run_simulation(config_manager, args.duration)
            
        elif args.mode == "api":
            app = create_api_server(config_manager)
            logger.info(f"Starting API server on {args.host}:{args.port}")
            import uvicorn
            uvicorn.run(app, host=args.host, port=args.port)
        
        else:
            logger.error(f"Unknown mode: {args.mode}")
            
    except Exception as e:
        logger.error(f"Error in {args.mode} mode: {e}")
        if args.log_level.upper() == "DEBUG":
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
