# Model Performance Report

Generated on: 2026-04-10 12:19:04

## Overall Performance Metrics

| Metric | Value |
|--------|-------|
| R² | 0.9964 |
| RMSE | 3.5391 |
| MAE | 0.7543 |
| MAPE | 195048083326245792.00% |
| Explained Variance | 0.9964 |
| Prediction Speed | 153100 samples/sec |

## Accuracy Metrics

| Threshold | Accuracy |
|-----------|----------|
| ±5 cycles | 97.02% |
| ±10 cycles | 98.10% |
| ±20 cycles | 98.95% |
| ±50 cycles | 100.00% |

## Cross-Engine Performance

- **Total Engines**: 50
- **Average R² per Engine**: 0.9964
- **R² Standard Deviation**: 0.0090
- **Cross-Engine Stability**: 0.9910
- **Engines with R² > 0.8**: 50/50
- **Engines with R² > 0.6**: 50/50

## Feature Importance

### Top 10 Features

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | life_ratio | 0.4374 |
| 2 | health_x_life | 0.3267 |
| 3 | health_index | 0.0869 |
| 4 | s2_x_s3 | 0.0578 |
| 5 | cycle | 0.0321 |
| 6 | s1_x_s3 | 0.0139 |
| 7 | s2_roll_median | 0.0081 |
| 8 | s1_x_s2 | 0.0053 |
| 9 | engine_id | 0.0035 |
| 10 | s3_roll_median | 0.0028 |

## Cross-Validation Results

- **Mean CV R²**: 0.9967
- **CV R² Standard Deviation**: 0.0014
- **CV Stability**: 0.9986

## Visualizations

- [Predictions Vs Actual](performance_results\predictions_vs_actual.png)
- [Residual Analysis](performance_results\residual_analysis.png)
- [Per Engine Performance](performance_results\per_engine_performance.png)
- [Feature Importance](performance_results\feature_importance.png)
- [Cv Results](performance_results\cv_results.png)
- [Error Distribution](performance_results\error_distribution.png)

## Summary

The model demonstrates **excellent performance** with:
- **R²**: 0.9964 (Target: >0.8)
- **RMSE**: 3.5391 (Target: <15)
- **Cross-Engine Stability**: 0.9910
- **CV Stability**: 0.9986

**Status: PRODUCTION READY**
