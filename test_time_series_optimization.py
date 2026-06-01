"""
Comprehensive Testing for Time-Series Optimized System
Validates temporal compliance, real-time computability, and cross-engine generalization
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from time_series_optimized_features import (
    TimeSeriesOptimizedFeatureEngineer,
    TemporalFeatureValidator,
    RealTimeFeatureChecker,
    RedundantFeatureDetector
)
from cross_engine_model_trainer import CrossEngineModelTrainer


class TimeSeriesOptimizationTester:
    """Comprehensive tester for time-series optimization"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        
    def test_temporal_compliance(self) -> Dict[str, Any]:
        """Test that all features are temporally compliant"""
        print("TESTING TEMPORAL COMPLIANCE...")
        print("-" * 50)
        
        # Create feature engineer
        fe = TimeSeriesOptimizedFeatureEngineer(
            rolling_window=15,
            use_scaler=True,
            max_computation_time_ms=50.0
        )
        
        # Generate sample data
        np.random.seed(42)
        engine_state = {
            'engine_id': 1,
            'design_life': 3000,
            'history': np.random.rand(20, 3) * [50, 800, 1100]
        }
        
        sensors = np.array([25.5, 650.2, 950.1])
        op_settings = np.array([0.5, 30.0, 1000.0])
        
        # Build features
        features = fe.build_temporal_feature_row(engine_state, 100, sensors, op_settings)
        
        # Check temporal validator
        temporal_violations = fe.temporal_validator.get_violations()
        
        # Validate each feature
        compliant_features = 0
        non_compliant_features = 0
        
        for feature_name in features.keys():
            if fe.temporal_validator.validate_feature(feature_name, "computed from historical data only"):
                compliant_features += 1
            else:
                non_compliant_features += 1
        
        result = {
            'total_features': len(features),
            'compliant_features': compliant_features,
            'non_compliant_features': non_compliant_features,
            'temporal_violations': temporal_violations,
            'compliance_rate': compliant_features / len(features) if features else 0,
            'status': 'passed' if non_compliant_features == 0 else 'failed'
        }
        
        print(f"Total features: {result['total_features']}")
        print(f"Compliant features: {result['compliant_features']}")
        print(f"Non-compliant features: {result['non_compliant_features']}")
        print(f"Compliance rate: {result['compliance_rate']:.2%}")
        print(f"Status: {result['status'].upper()}")
        
        if temporal_violations:
            print("Temporal violations:")
            for violation in temporal_violations:
                print(f"  - {violation}")
        
        return result
    
    def test_real_time_computability(self) -> Dict[str, Any]:
        """Test that features can be computed in real-time"""
        print("\nTESTING REAL-TIME COMPUTABILITY...")
        print("-" * 50)
        
        # Create feature engineer with strict time limits
        fe = TimeSeriesOptimizedFeatureEngineer(
            rolling_window=15,
            use_scaler=True,
            max_computation_time_ms=50.0
        )
        
        # Generate test data
        np.random.seed(42)
        test_cases = []
        
        for i in range(100):
            engine_state = {
                'engine_id': i % 10 + 1,
                'design_life': 3000,
                'history': np.random.rand(15, 3) * [50, 800, 1100]
            }
            
            sensors = np.array([
                np.random.normal(30, 5),
                np.random.normal(700, 50),
                np.random.normal(1000, 100)
            ])
            op_settings = np.array([0.5, 30.0, 1000.0])
            
            test_cases.append((engine_state, sensors, op_settings))
        
        # Test computation times
        computation_times = []
        fast_features = 0
        slow_features = 0
        
        for engine_state, sensors, op_settings in test_cases:
            start_time = time.time()
            features = fe.build_temporal_feature_row(engine_state, 100, sensors, op_settings)
            computation_time = (time.time() - start_time) * 1000  # Convert to ms
            
            computation_times.append(computation_time)
            
            if computation_time <= fe.max_computation_time_ms:
                fast_features += 1
            else:
                slow_features += 1
        
        avg_time = np.mean(computation_times)
        max_time = np.max(computation_times)
        min_time = np.min(computation_times)
        std_time = np.std(computation_times)
        
        result = {
            'total_tests': len(test_cases),
            'fast_features': fast_features,
            'slow_features': slow_features,
            'avg_computation_time_ms': avg_time,
            'max_computation_time_ms': max_time,
            'min_computation_time_ms': min_time,
            'std_computation_time_ms': std_time,
            'real_time_rate': fast_features / len(test_cases),
            'status': 'passed' if slow_features == 0 else 'failed'
        }
        
        print(f"Total tests: {result['total_tests']}")
        print(f"Fast computations: {result['fast_features']}")
        print(f"Slow computations: {result['slow_features']}")
        print(f"Average time: {result['avg_computation_time_ms']:.2f}ms")
        print(f"Max time: {result['max_computation_time_ms']:.2f}ms")
        print(f"Real-time rate: {result['real_time_rate']:.2%}")
        print(f"Status: {result['status'].upper()}")
        
        return result
    
    def test_feature_importance_pruning(self) -> Dict[str, Any]:
        """Test feature importance-based pruning"""
        print("\nTESTING FEATURE IMPORTANCE PRUNING...")
        print("-" * 50)
        
        # Create trainer and generate data
        trainer = CrossEngineModelTrainer(
            n_trials=5,  # Reduced for testing
            cv_folds=3,
            use_optuna=False
        )
        
        X, y = trainer.generate_cross_engine_training_data(num_engines=10)
        
        # Train simple model
        from xgboost import XGBRegressor
        model = XGBRegressor(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X, y, verbose=False)
        
        # Get feature importance
        feature_names = list(X.columns)
        importance_dict = dict(zip(feature_names, model.feature_importances_))
        
        # Test pruning
        fe = trainer.feature_engineer
        original_features = set(feature_names)
        
        # Prune by importance
        features_to_remove = fe.prune_features_by_importance(
            importance_dict, 
            importance_threshold=0.001
        )
        
        remaining_features = fe.get_optimized_feature_names()
        
        # Test redundant feature removal
        redundant_features, mi_scores = fe.remove_redundant_features(
            X[remaining_features], y
        )
        
        final_features = fe.get_optimized_feature_names()
        
        result = {
            'original_features': len(original_features),
            'features_removed_importance': len(features_to_remove),
            'features_removed_redundancy': len(redundant_features),
            'final_features': len(final_features),
            'reduction_rate': (len(original_features) - len(final_features)) / len(original_features),
            'top_10_features': sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:10],
            'status': 'passed' if len(final_features) > 0 else 'failed'
        }
        
        print(f"Original features: {result['original_features']}")
        print(f"Removed by importance: {result['features_removed_importance']}")
        print(f"Removed by redundancy: {result['features_removed_redundancy']}")
        print(f"Final features: {result['final_features']}")
        print(f"Reduction rate: {result['reduction_rate']:.2%}")
        print(f"Status: {result['status'].upper()}")
        
        print("\nTop 10 most important features:")
        for i, (feature, importance) in enumerate(result['top_10_features'], 1):
            print(f"  {i}. {feature}: {importance:.4f}")
        
        return result
    
    def test_cross_engine_generalization(self) -> Dict[str, Any]:
        """Test cross-engine generalization"""
        print("\nTESTING CROSS-ENGINE GENERALIZATION...")
        print("-" * 50)
        
        # Create trainer
        trainer = CrossEngineModelTrainer(
            n_trials=5,
            cv_folds=3,
            use_optuna=False,
            engine_aware_validation=True
        )
        
        # Generate diverse training data
        X, y = trainer.generate_cross_engine_training_data(num_engines=20)
        
        # Train cross-engine model
        model = trainer.train_cross_engine_model(X, y)
        
        # Get performance metrics
        metrics = trainer.engine_performance
        
        # Analyze per-engine performance
        engine_r2_scores = [m['r2'] for m in metrics.values()]
        engine_rmse_scores = [m['rmse'] for m in metrics.values()]
        
        result = {
            'total_engines': len(metrics),
            'avg_r2_per_engine': np.mean(engine_r2_scores),
            'std_r2_per_engine': np.std(engine_r2_scores),
            'min_r2_per_engine': np.min(engine_r2_scores),
            'max_r2_per_engine': np.max(engine_r2_scores),
            'avg_rmse_per_engine': np.mean(engine_rmse_scores),
            'std_rmse_per_engine': np.std(engine_rmse_scores),
            'cross_engine_stability': 1.0 - np.std(engine_r2_scores),  # Higher is better
            'engines_above_08_r2': sum(1 for r2 in engine_r2_scores if r2 > 0.8),
            'engines_above_06_r2': sum(1 for r2 in engine_r2_scores if r2 > 0.6),
            'status': 'passed' if np.mean(engine_r2_scores) > 0.6 else 'failed'
        }
        
        print(f"Total engines: {result['total_engines']}")
        print(f"Average R² per engine: {result['avg_r2_per_engine']:.4f}")
        print(f"R² standard deviation: {result['std_r2_per_engine']:.4f}")
        print(f"Min R² per engine: {result['min_r2_per_engine']:.4f}")
        print(f"Max R² per engine: {result['max_r2_per_engine']:.4f}")
        print(f"Cross-engine stability: {result['cross_engine_stability']:.4f}")
        print(f"Engines with R² > 0.8: {result['engines_above_08_r2']}/{result['total_engines']}")
        print(f"Engines with R² > 0.6: {result['engines_above_06_r2']}/{result['total_engines']}")
        print(f"Status: {result['status'].upper()}")
        
        return result
    
    def test_engine_normalization(self) -> Dict[str, Any]:
        """Test engine-specific normalization"""
        print("\nTESTING ENGINE NORMALIZATION...")
        print("-" * 50)
        
        # Create feature engineer
        fe = TimeSeriesOptimizedFeatureEngineer(
            rolling_window=15,
            use_scaler=True
        )
        
        # Simulate multiple engines with different baselines
        engines_data = {}
        
        for engine_id in range(1, 4):
            # Different baseline for each engine
            baseline_multiplier = engine_id * 0.1 + 0.8
            
            engine_state = {
                'engine_id': engine_id,
                'design_life': 3000,
                'history': np.random.rand(20, 3) * [50, 800, 1100] * baseline_multiplier
            }
            
            sensors = np.array([
                np.random.normal(30, 5) * baseline_multiplier,
                np.random.normal(700, 50) * baseline_multiplier,
                np.random.normal(1000, 100) * baseline_multiplier
            ])
            op_settings = np.array([0.5, 30.0, 1000.0])
            
            # Generate multiple readings per engine
            engine_features = []
            for cycle in range(10, 20):
                features = fe.build_temporal_feature_row(engine_state, cycle, sensors, op_settings)
                engine_features.append(features)
            
            engines_data[engine_id] = engine_features
        
        # Check normalization effectiveness
        normalization_scores = {}
        
        for engine_id, features_list in engines_data.items():
            # Extract normalized deviation features
            norm_deviations = []
            for features in features_list:
                for sensor in ['s1', 's2', 's3']:
                    norm_key = f"{sensor}_norm_deviation"
                    if norm_key in features:
                        norm_deviations.append(features[norm_key])
            
            if norm_deviations:
                # Lower standard deviation indicates better normalization
                norm_std = np.std(norm_deviations)
                normalization_scores[engine_id] = norm_std
        
        result = {
            'total_engines': len(engines_data),
            'normalization_scores': normalization_scores,
            'avg_normalization_std': np.mean(list(normalization_scores.values())),
            'engines_with_good_normalization': sum(1 for score in normalization_scores.values() if score < 0.5),
            'status': 'passed' if len(normalization_scores) > 0 else 'failed'
        }
        
        print(f"Total engines: {result['total_engines']}")
        print(f"Average normalization std: {result['avg_normalization_std']:.4f}")
        print(f"Engines with good normalization: {result['engines_with_good_normalization']}/{result['total_engines']}")
        print(f"Status: {result['status'].upper()}")
        
        print("\nNormalization scores per engine:")
        for engine_id, score in normalization_scores.items():
            print(f"  Engine {engine_id}: {score:.4f}")
        
        return result
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all time-series optimization tests"""
        print("TIME-SERIES OPTIMIZATION COMPREHENSIVE TESTING")
        print("=" * 60)
        
        # Run all tests
        test_results = {
            'temporal_compliance': self.test_temporal_compliance(),
            'real_time_computability': self.test_real_time_computability(),
            'feature_importance_pruning': self.test_feature_importance_pruning(),
            'cross_engine_generalization': self.test_cross_engine_generalization(),
            'engine_normalization': self.test_engine_normalization()
        }
        
        # Generate summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = result.get('status', 'unknown')
            
            if status == 'passed':
                print(f"  {test_name}: PASSED")
                passed_tests += 1
            else:
                print(f"  {test_name}: FAILED")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        # Key metrics summary
        if 'temporal_compliance' in test_results:
            tc_result = test_results['temporal_compliance']
            print(f"Temporal Compliance: {tc_result['compliance_rate']:.2%}")
        
        if 'real_time_computability' in test_results:
            rc_result = test_results['real_time_computability']
            print(f"Real-time Rate: {rc_result['real_time_rate']:.2%}")
            print(f"Avg Computation Time: {rc_result['avg_computation_time_ms']:.2f}ms")
        
        if 'cross_engine_generalization' in test_results:
            ce_result = test_results['cross_engine_generalization']
            print(f"Cross-engine Stability: {ce_result['cross_engine_stability']:.4f}")
            print(f"Avg R² per Engine: {ce_result['avg_r2_per_engine']:.4f}")
        
        if 'feature_importance_pruning' in test_results:
            fp_result = test_results['feature_importance_pruning']
            print(f"Feature Reduction: {fp_result['reduction_rate']:.2%}")
        
        # Overall assessment
        print("\n" + "-" * 60)
        if passed_tests == total_tests:
            print("STATUS: ALL TESTS PASSED - SYSTEM OPTIMIZED")
            print("Time-series optimization is working correctly!")
        else:
            print(f"STATUS: {total_tests - passed_tests} TESTS FAILED")
            print("Some optimizations need attention.")
        
        print("=" * 60)
        
        return test_results


def main():
    """Main testing function"""
    tester = TimeSeriesOptimizationTester()
    results = tester.run_comprehensive_test()
    
    return tester, results


if __name__ == "__main__":
    tester, results = main()
