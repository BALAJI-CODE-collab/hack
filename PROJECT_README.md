"""
✅ COMPLETE POACHING ACTIVITY PREDICTION ML PIPELINE

This project includes:
1. ✓ End-to-end ML pipeline from data to predictions
2. ✓ Sample data generation for parks, roads, villages, water, incidents, rainfall, moon phases
3. ✓ Data preprocessing and validation
4. ✓ Spatial grid creation and assignment
5. ✓ Feature engineering (static + dynamic + temporal)
6. ✓ Random Forest + XGBoost model training with hyperparameter tuning
7. ✓ SMOTE-based class imbalance handling
8. ✓ Ensemble predictions with probability averaging
9. ✓ GIS heatmap visualization using GeoJSON and Folium
10. ✓ Patrol priority zone identification
11. ✓ Confusion matrix and feature importance plots
12. ✓ Complete evaluation metrics (AUC, Precision, Recall, F1)

PROJECT STRUCTURE:
- data/                    - Raw and generated datasets
  - generate_sample_data.py  - Sample data generation
  - park_boundary.geojson    - Park boundary
  - poaching_incidents.csv   - Incident records
  - rainfall.csv             - Weekly rainfall
  - moon_phases.csv          - Moon phase data
  
- preprocessing/           - Data loading and preprocessing
  - load_data.py            - Loaders for all data types
  - grid.py                 - Spatial grid creation
  - __init__.py             - DataPreprocessor class
  
- feature_engineering/     - Feature engineering
  - __init__.py             - FeatureEngineer class
  - Computes: distances, NDVI, rainfall, moon, lag features
  
- models/                  - Model training
  - __init__.py             - PoachedModelTrainer class
  - Trains RF + XGBoost
  - Creates ensemble
  
- evaluation/              - Model evaluation
  - evaluate.py             - Evaluation metrics
  
- visualization/           - Visualization
  - __init__.py             - PoachedVisualizer class
  - GIS heatmaps, maps, plots
  
- main_pipeline.py         - Complete orchestrator
  
RUNNING THE PIPELINE:
    python main_pipeline.py

OUTPUTS GENERATED:
  • outputs/risk_heatmap.geojson       - GIS-ready heatmap (risk probabilities)
  • outputs/risk_map.html              - Interactive Leaflet map
  • outputs/confusion_matrix.png       - Model evaluation visualization
  • outputs/feature_importance.png     - Feature importance 
  • outputs/patrol_priority_zones.csv  - Top 15 high-risk cells
  • models/random_forest_model.pkl     - Trained RF classifier
  • models/xgboost_model.pkl           - Trained XGB classifier
  • models/evaluation_metrics.json     - AUC, precision, recall, F1

DELIVERABLES:
✅ Clean, modular Python code with complete documentation
✅ Reproducible ML pipeline with stratified train-test splits
✅ GIS heatmap output (GeoJSON + interactive Folium map)
✅ Patrol priority grid list ranked by risk
✅ Ensemble model combining RF + XGBoost
✅ Target AUC > 0.8 achievable with this architecture
✅ SMOTE resampling for handling class imbalance
✅ Hyperparameter tuning for both models

OPTIONS FOR IMPROVEMENT:
1. Real poaching data (currently using synthetic data)
2. Higher-resolution spatial grid (currently 1°)
3. More features (vegetation indices, human proximity, etc.)
4. Temporal anomaly detection
5. External risk factors (hunting season, ranger patrols, etc.)
6. Model stacking for potentially better ensemble
7. Deep learning variants (LSTM for time series patterns)
"""

print(__doc__)
