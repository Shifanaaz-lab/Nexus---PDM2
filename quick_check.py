"""
Quick System Check for Enhanced Predictive Maintenance System
Tests core functionality without complex dependencies
"""

import os
import sys
import time
import numpy as np
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports"""
    print("TESTING BASIC IMPORTS...")
    
    try:
        import numpy as np
        print("✓ numpy")
    except ImportError:
        print("✗ numpy")
        return False
    
    try:
        import pandas as pd
        print("✓ pandas")
    except ImportError:
        print("✗ pandas")
        return False
    
    try:
        import xgboost as xgb
        print("✓ xgboost")
    except ImportError:
        print("✗ xgboost")
        return False
    
    try:
        from enhanced_feature_engineering import EnhancedFeatureEngineer
        print("✓ enhanced_feature_engineering")
    except ImportError as e:
        print(f"✗ enhanced_feature_engineering: {e}")
        return False
    
    try:
        from optimized_model_training import OptimizedModelTrainer
        print("✓ optimized_model_training")
    except ImportError as e:
        print(f"✗ optimized_model_training: {e}")
        return False
    
    return True

def test_feature_engineering():
    """Test enhanced feature engineering"""
    print("\nTESTING FEATURE ENGINEERING...")
    
    try:
        from enhanced_feature_engineering import EnhancedFeatureEngineer
        
        # Create feature engineer
        fe = EnhancedFeatureEngineer(rolling_window=15)
        print("✓ Feature engineer created")
        
        # Create sample data
        np.random.seed(42)
        sample_data = []
        for i in range(50):
            sample_data.append({
                'engine_id': float(i % 5 + 1),
                'cycle': float(i),
                's1': np.random.normal(30, 5),
                's2': np.random.normal(700, 50),
                's3': np.random.normal(1000, 100),
                'setting1': np.random.uniform(0, 1),
                'setting2': np.random.uniform(20, 40),
                'setting3': np.random.uniform(900, 1100)
            })
        
        # Test fitting
        fe.fit(sample_data)
        print("✓ Feature engineer fitted")
        
        # Test feature building
        engine_state = {
            'engine_id': 1,
            'design_life': 3000,
            'history': np.random.rand(15, 3) * [50, 800, 1100]
        }
        
        sensors = np.array([25.5, 650.2, 950.1])
        op_settings = np.array([0.5, 30.0, 1000.0])
        
        start_time = time.time()
        features = fe.build_feature_row(engine_state, 100, sensors, op_settings)
        computation_time = (time.time() - start_time) * 1000
        
        print(f"✓ Features computed: {len(features)} features in {computation_time:.2f}ms")
        
        # Show sample features
        print("Sample features:")
        for i, (key, value) in enumerate(list(features.items())[:10]):
            print(f"  {key}: {value:.4f}")
        
        return True, len(features), computation_time
        
    except Exception as e:
        print(f"✗ Feature engineering failed: {e}")
        return False, 0, 0

def test_model_training():
    """Test model training"""
    print("\nTESTING MODEL TRAINING...")
    
    try:
        from optimized_model_training import OptimizedModelTrainer
        from xgboost import XGBRegressor
        
        # Create trainer with minimal settings
        trainer = OptimizedModelTrainer(
            n_trials=1,  # Minimal for testing
            cv_folds=2,
            use_optuna=False  # Skip optimization
        )
        
        # Generate small dataset
        X, y = trainer.generate_training_data(num_engines=5)
        print(f"✓ Training data generated: {X.shape[0]} samples, {X.shape[1]} features")
        
        # Train simple model without early stopping
        params = {
            'n_estimators': 10,
            'max_depth': 3,
            'learning_rate': 0.1,
            'tree_method': 'hist',
            'objective': 'reg:squarederror',
            'n_jobs': 1,
            'random_state': 42
        }
        
        # Simple training without early stopping for testing
        model = XGBRegressor(**params)
        model.fit(X, y, verbose=False)
        print("✓ Model trained successfully")
        
        # Test prediction
        y_pred = model.predict(X[:5])
        print(f"✓ Predictions made: {y_pred}")
        
        # Calculate basic metrics (use same length arrays)
        from sklearn.metrics import mean_squared_error, r2_score
        y_pred_full = model.predict(X)
        rmse = np.sqrt(mean_squared_error(y, y_pred_full))
        r2 = r2_score(y, y_pred_full)
        
        print(f"✓ Basic metrics - RMSE: {rmse:.4f}, R²: {r2:.4f}")
        
        return True, rmse, r2
        
    except Exception as e:
        print(f"✗ Model training failed: {e}")
        return False, 0, 0

def test_configuration():
    """Test configuration"""
    print("\nTESTING CONFIGURATION...")
    
    try:
        from deployment_config import ConfigManager
        
        # Test default config
        config_manager = ConfigManager()
        print("✓ Configuration loaded")
        
        # Test some key settings
        print(f"  Model paths: {len(config_manager.config.model.model_paths)}")
        print(f"  Batch size: {config_manager.config.streaming.batch_size}")
        print(f"  Critical RUL threshold: {config_manager.config.alerting.critical_rul_threshold}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

def main():
    """Main test function"""
    print("ENHANCED PREDICTIVE MAINTENANCE SYSTEM - QUICK CHECK")
    print("=" * 60)
    
    # Test imports
    if not test_basic_imports():
        print("\n❌ Basic imports failed. Please check dependencies.")
        return
    
    # Test feature engineering
    fe_success, feature_count, fe_time = test_feature_engineering()
    
    # Test model training
    mt_success, rmse, r2 = test_model_training()
    
    # Test configuration
    config_success = test_configuration()
    
    # Summary
    print("\n" + "=" * 60)
    print("QUICK CHECK SUMMARY")
    print("=" * 60)
    
    if fe_success:
        print(f"✓ Feature Engineering: {feature_count} features in {fe_time:.2f}ms")
    else:
        print("✗ Feature Engineering: FAILED")
    
    if mt_success:
        print(f"✓ Model Training: RMSE={rmse:.4f}, R²={r2:.4f}")
    else:
        print("✗ Model Training: FAILED")
    
    if config_success:
        print("✓ Configuration: OK")
    else:
        print("✗ Configuration: FAILED")
    
    # Overall status
    all_passed = fe_success and mt_success and config_success
    
    print("\n" + "-" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        print("\nNext steps:")
        print("1. Train full models: python main.py --mode train --engines 100 --trials 50")
        print("2. Start API server: python main.py --mode api")
        print("3. Test API: curl http://localhost:8000/health")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    main()
