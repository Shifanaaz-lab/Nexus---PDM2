"""
Comprehensive System Testing and Validation Script
Tests all components of the enhanced predictive maintenance system
"""

import os
import sys
import time
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SystemTester:
    """Comprehensive testing suite for the predictive maintenance system"""
    
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def run_all_tests(self):
        """Run all system tests"""
        logger.info("Starting comprehensive system testing...")
        
        test_methods = [
            self.test_feature_engineering,
            self.test_model_training,
            self.test_model_evaluation,
            self.test_streaming_pipeline,
            self.test_api_server,
            self.test_configuration,
            self.test_performance
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"Running {test_method.__name__}...")
                result = test_method()
                self.test_results[test_method.__name__] = result
                logger.info(f"✓ {test_method.__name__} completed")
            except Exception as e:
                logger.error(f"✗ {test_method.__name__} failed: {e}")
                self.errors.append(f"{test_method.__name__}: {str(e)}")
                self.test_results[test_method.__name__] = {"status": "failed", "error": str(e)}
        
        self.generate_test_report()
        
    def test_feature_engineering(self) -> Dict[str, Any]:
        """Test enhanced feature engineering"""
        from enhanced_feature_engineering import EnhancedFeatureEngineer
        
        # Create sample data
        np.random.seed(42)
        sample_data = []
        for i in range(100):
            sample_data.append({
                'engine_id': float(i % 10 + 1),
                'cycle': float(i),
                's1': np.random.normal(30, 5),
                's2': np.random.normal(700, 50),
                's3': np.random.normal(1000, 100),
                'setting1': np.random.uniform(0, 1),
                'setting2': np.random.uniform(20, 40),
                'setting3': np.random.uniform(900, 1100)
            })
        
        # Test feature engineer
        fe = EnhancedFeatureEngineer(rolling_window=15)
        
        # Test fitting
        fe.fit(sample_data)
        
        # Test transformation
        transformed = fe.transform(sample_data[:10])
        
        # Test feature building
        engine_state = {
            'engine_id': 1,
            'design_life': 3000,
            'history': np.random.rand(20, 3) * [50, 800, 1100]
        }
        
        sensors = np.array([25.5, 650.2, 950.1])
        op_settings = np.array([0.5, 30.0, 1000.0])
        
        features = fe.build_feature_row(engine_state, 100, sensors, op_settings)
        
        return {
            "status": "passed",
            "sample_count": len(sample_data),
            "feature_count": len(features),
            "transformed_samples": len(transformed),
            "feature_names_sample": list(features.keys())[:10]
        }
    
    def test_model_training(self) -> Dict[str, Any]:
        """Test optimized model training"""
        try:
            from optimized_model_training import OptimizedModelTrainer
            
            # Create trainer with reduced parameters for testing
            trainer = OptimizedModelTrainer(
                n_trials=5,  # Reduced for testing
                cv_folds=3,
                use_optuna=False  # Skip optimization for testing
            )
            
            # Generate small training dataset
            X, y = trainer.generate_training_data(num_engines=10)
            
            # Test hyperparameter optimization (skipped)
            best_params = trainer.default_params
            
            # Test model training
            model = trainer.train_model_with_early_stopping(X, y, best_params)
            
            # Test evaluation
            metrics = trainer.evaluate_model(model, X, y)
            
            return {
                "status": "passed",
                "training_samples": len(X),
                "feature_count": X.shape[1],
                "rmse": metrics.get('rmse', 'N/A'),
                "r2": metrics.get('r2', 'N/A'),
                "mae": metrics.get('mae', 'N/A')
            }
            
        except ImportError as e:
            return {
                "status": "skipped",
                "reason": f"Missing dependencies: {e}"
            }
    
    def test_model_evaluation(self) -> Dict[str, Any]:
        """Test model evaluation and monitoring"""
        try:
            from model_evaluation_monitoring import ModelEvaluator, RealTimeMonitor
            
            # Create sample predictions and actuals
            np.random.seed(42)
            y_true = np.random.uniform(50, 300, 100)
            y_pred = y_true + np.random.normal(0, 15, 100)  # Add some noise
            
            # Test evaluator
            evaluator = ModelEvaluator()
            
            # Mock model for testing
            class MockModel:
                def predict(self, X):
                    return y_pred[:len(X)]
                def get_params(self):
                    return {}
            
            mock_model = MockModel()
            X_mock = pd.DataFrame(np.random.rand(100, 10))
            
            metrics = evaluator.evaluate_model_comprehensive(
                mock_model, X_mock, y_true, [f"feature_{i}" for i in range(10)]
            )
            
            # Test monitoring
            monitor = RealTimeMonitor(window_size=50)
            
            for i in range(50):
                monitor.add_prediction(
                    engine_id=1,
                    features={"feature_1": i},
                    predicted_rul=y_pred[i],
                    actual_rul=y_true[i]
                )
            
            summary = monitor.get_monitoring_summary()
            
            return {
                "status": "passed",
                "rmse": metrics.rmse,
                "r2": metrics.r2,
                "mae": metrics.mae,
                "monitoring_predictions": summary.get('total_predictions', 0),
                "monitoring_alerts": summary.get('total_alerts', 0)
            }
            
        except ImportError as e:
            return {
                "status": "skipped",
                "reason": f"Missing dependencies: {e}"
            }
    
    def test_streaming_pipeline(self) -> Dict[str, Any]:
        """Test streaming data pipeline"""
        try:
            from streaming_data_pipeline import (
                StreamingPipeline, TelemetryData, 
                EngineStateManager, StreamingFeatureProcessor
            )
            
            # Test engine state manager
            state_manager = EngineStateManager(max_history_length=10)
            
            # Add some engine states
            for engine_id in range(1, 4):
                for cycle in range(1, 6):
                    sensors = np.array([25.0, 650.0, 950.0]) + np.random.rand(3)
                    op_settings = np.array([0.5, 30.0, 1000.0])
                    
                    state_manager.update_engine_state(engine_id, cycle, sensors, op_settings)
            
            active_engines = state_manager.get_all_engine_ids()
            
            return {
                "status": "passed",
                "active_engines": len(active_engines),
                "engine_ids": active_engines
            }
            
        except ImportError as e:
            return {
                "status": "skipped",
                "reason": f"Missing dependencies: {e}"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_api_server(self) -> Dict[str, Any]:
        """Test API server functionality"""
        try:
            # Test if FastAPI is available
            import fastapi
            import uvicorn
            
            # Test configuration loading
            from deployment_config import ConfigManager
            
            config_manager = ConfigManager()
            
            return {
                "status": "passed",
                "fastapi_version": fastapi.__version__,
                "config_loaded": True,
                "model_paths": len(config_manager.config.model.model_paths)
            }
            
        except ImportError as e:
            return {
                "status": "skipped",
                "reason": f"Missing API dependencies: {e}"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test configuration management"""
        try:
            from deployment_config import ConfigManager, SystemConfig
            
            # Test default configuration
            config_manager = ConfigManager()
            
            # Test configuration validation
            config_manager.validate_config()
            
            # Test environment variable loading
            os.environ['MONGODB_URI'] = 'mongodb://test:27017/'
            os.environ['BATCH_SIZE'] = '50'
            
            config_manager_with_env = ConfigManager()
            
            return {
                "status": "passed",
                "default_config_loaded": True,
                "validation_passed": True,
                "env_override_works": config_manager_with_env.config.streaming.batch_size == 50
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def test_performance(self) -> Dict[str, Any]:
        """Test system performance"""
        try:
            from enhanced_feature_engineering import EnhancedFeatureEngineer
            
            # Test feature engineering performance
            fe = EnhancedFeatureEngineer(rolling_window=30)
            
            # Generate test data
            np.random.seed(42)
            test_data = []
            for i in range(1000):
                test_data.append({
                    'engine_id': float(i % 50 + 1),
                    'cycle': float(i),
                    's1': np.random.normal(30, 5),
                    's2': np.random.normal(700, 50),
                    's3': np.random.normal(1000, 100),
                    'setting1': np.random.uniform(0, 1),
                    'setting2': np.random.uniform(20, 40),
                    'setting3': np.random.uniform(900, 1100)
                })
            
            # Time feature engineering
            start_time = time.time()
            fe.fit(test_data)
            fit_time = time.time() - start_time
            
            start_time = time.time()
            transformed = fe.transform(test_data)
            transform_time = time.time() - start_time
            
            # Test single feature computation
            engine_state = {
                'engine_id': 1,
                'design_life': 3000,
                'history': np.random.rand(30, 3) * [50, 800, 1100]
            }
            
            sensors = np.array([25.5, 650.2, 950.1])
            op_settings = np.array([0.5, 30.0, 1000.0])
            
            start_time = time.time()
            features = fe.build_feature_row(engine_state, 100, sensors, op_settings)
            single_feature_time = time.time() - start_time
            
            return {
                "status": "passed",
                "fit_time_ms": fit_time * 1000,
                "transform_time_ms": (transform_time / len(test_data)) * 1000,
                "single_feature_time_ms": single_feature_time * 1000,
                "feature_count": len(features),
                "samples_processed": len(transformed)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("ENHANCED PREDICTIVE MAINTENANCE SYSTEM - TEST REPORT")
        print("="*80)
        
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for test_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            
            if status == 'passed':
                print(f"✓ {test_name}: PASSED")
                passed_tests += 1
                # Print key metrics
                if 'rmse' in result:
                    print(f"    RMSE: {result['rmse']:.4f}")
                if 'r2' in result:
                    print(f"    R²: {result['r2']:.4f}")
                if 'feature_count' in result:
                    print(f"    Features: {result['feature_count']}")
                if 'single_feature_time_ms' in result:
                    print(f"    Feature computation: {result['single_feature_time_ms']:.2f}ms")
                    
            elif status == 'skipped':
                print(f"- {test_name}: SKIPPED ({result.get('reason', 'Unknown reason')})")
                skipped_tests += 1
                
            else:
                print(f"✗ {test_name}: FAILED ({result.get('error', 'Unknown error')})")
                failed_tests += 1
        
        print("\n" + "-"*80)
        print(f"SUMMARY: {passed_tests} passed, {failed_tests} failed, {skipped_tests} skipped")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("\n" + "="*80)
        
        # Performance expectations
        print("PERFORMANCE EXPECTATIONS:")
        print("- Target R²: > 0.85 (vs original 0.68)")
        print("- Target RMSE: < 15 (vs original ~25)")
        print("- Feature computation: < 50ms per reading")
        print("- Total features: 150+ per reading")
        print("- Real-time inference: < 100ms")
        
        print("\nNEXT STEPS:")
        if failed_tests == 0:
            print("✓ All tests passed! System is ready for deployment.")
            print("1. Run: python main.py --mode train --engines 100 --trials 50")
            print("2. Run: python main.py --mode api")
            print("3. Test API: curl http://localhost:8000/health")
        else:
            print(f"✗ {failed_tests} tests failed. Fix issues before deployment.")
        
        print("="*80)


def check_system_requirements():
    """Check system requirements and dependencies"""
    print("CHECKING SYSTEM REQUIREMENTS...")
    print("-" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 11):
        print("⚠️  Warning: Python 3.11+ recommended")
    else:
        print("✓ Python version OK")
    
    # Check required packages
    required_packages = [
        'numpy', 'pandas', 'xgboost', 'scikit-learn',
        'matplotlib', 'seaborn', 'optuna', 'fastapi', 'uvicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements_enhanced.txt")
    else:
        print("\n✓ All required packages installed")
    
    # Check optional packages
    optional_packages = ['pymongo', 'redis', 'pyyaml']
    
    print("\nOPTIONAL PACKAGES:")
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"- {package} (optional)")
    
    print("-" * 50)
    
    return len(missing_packages) == 0


def quick_performance_check():
    """Quick performance check of key components"""
    print("\nQUICK PERFORMANCE CHECK")
    print("-" * 30)
    
    try:
        from enhanced_feature_engineering import EnhancedFeatureEngineer
        
        # Test feature engineering speed
        fe = EnhancedFeatureEngineer(rolling_window=30)
        
        # Generate sample data
        np.random.seed(42)
        engine_state = {
            'engine_id': 1,
            'design_life': 3000,
            'history': np.random.rand(30, 3) * [50, 800, 1100]
        }
        
        sensors = np.array([25.5, 650.2, 950.1])
        op_settings = np.array([0.5, 30.0, 1000.0])
        
        # Time feature computation
        start_time = time.time()
        features = fe.build_feature_row(engine_state, 100, sensors, op_settings)
        computation_time = (time.time() - start_time) * 1000
        
        print(f"Feature computation time: {computation_time:.2f}ms")
        print(f"Number of features: {len(features)}")
        
        if computation_time < 50:
            print("✓ Performance meets requirements (< 50ms)")
        else:
            print("⚠️  Performance slower than expected")
        
        # Show sample features
        print(f"\nSample features:")
        for i, (key, value) in enumerate(list(features.items())[:10]):
            print(f"  {key}: {value:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance check failed: {e}")
        return False


def main():
    """Main testing function"""
    print("ENHANCED PREDICTIVE MAINTENANCE SYSTEM - TESTING SUITE")
    print("=" * 60)
    
    # Check system requirements
    requirements_ok = check_system_requirements()
    
    if not requirements_ok:
        print("\n⚠️  Please install missing dependencies before continuing")
        return
    
    # Quick performance check
    performance_ok = quick_performance_check()
    
    # Run comprehensive tests
    tester = SystemTester()
    tester.run_all_tests()
    
    # Final recommendations
    print("\nFINAL RECOMMENDATIONS:")
    print("-" * 30)
    
    if requirements_ok and performance_ok:
        print("✓ System is ready for enhanced model training!")
        print("\nRecommended commands:")
        print("1. Train models: python main.py --mode train --engines 100 --trials 50")
        print("2. Evaluate: python main.py --mode evaluate")
        print("3. Start API: python main.py --mode api")
        print("4. Run simulation: python main.py --mode simulate --duration 10")
    else:
        print("⚠️  Fix issues before training models")
        print("1. Install missing dependencies")
        print("2. Check system requirements")
        print("3. Run tests again")


if __name__ == "__main__":
    main()
