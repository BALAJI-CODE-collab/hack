"""
Main orchestrator for Poaching Activity Prediction ML Pipeline.

This script coordinates the complete workflow:
1. Generate sample data
2. Load and preprocess data
3. Create spatial grid
4. Engineer features
5. Train RF + XGBoost models
6. Evaluate ensemble
7. Generate visualizations
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing import DataPreprocessor
from preprocessing.grid import create_grid, assign_points_to_grid
from feature_engineering import FeatureEngineer
from models import PoachedModelTrainer
from visualization import PoachedVisualizer
from data.generate_sample_data import (
    generate_park_boundary, generate_roads, generate_villages, 
    generate_water, generate_poaching_incidents, generate_rainfall, 
    generate_moon_phases, generate_ndvi
)


def main(use_spatial_lag=True, use_feature_selection=True):
    print("\n" + "="*70)
    print(" POACHING ACTIVITY PREDICTION ML PIPELINE")
    print("="*70 + "\n")
    
    # ===== STEP 1: Generate Sample Data =====
    print(f"{'='*70}")
    print("STEP 1: Generating Sample Datasets")
    print(f"{'='*70}")
    
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Generate park boundary first
    park = generate_park_boundary(data_dir / 'park_boundary.geojson')
    
    # Generate all datasets
    generate_roads(data_dir / 'roads.geojson', park, num_roads=5)
    generate_villages(data_dir / 'villages.geojson', park, num_villages=8)
    generate_water(data_dir / 'water.geojson', park, num_waterbodies=4)
    generate_poaching_incidents(data_dir / 'poaching_incidents.csv', park, num_incidents=150)
    generate_rainfall(data_dir / 'rainfall.csv')
    generate_moon_phases(data_dir / 'moon_phases.csv')
    generate_ndvi(data_dir / 'ndvi.csv', park)
    
    # ===== STEP 2: Load & Preprocess Data =====
    print(f"\n{'='*70}")
    print("STEP 2: Loading and Preprocessing Data")
    print(f"{'='*70}\n")
    
    preprocessor = DataPreprocessor(str(data_dir))
    preprocessor.load_all()
    preprocessor.clip_to_park()
    preprocessor.validate_data()
    preprocessor.get_summary()
    
    # ===== STEP 3: Create Spatial Grid =====
    print(f"\n{'='*70}")
    print("STEP 3: Creating Spatial Grid")
    print(f"{'='*70}\n")
    
    grid_df = create_grid(preprocessor.park_boundary, cell_size_deg=0.3)  # ~30km cells for larger park
    print(f"[OK] Created {len(grid_df)} grid cells")
    
    # Assign poaching incidents to grid
    poaching_with_grid = assign_points_to_grid(preprocessor.poaching, grid_df)
    preprocessor.poaching = poaching_with_grid
    
    # ===== STEP 4: Feature Engineering =====
    print(f"\n{'='*70}")
    print("STEP 4: Feature Engineering")
    print(f"{'='*70}\n")
    
    feature_engineer = FeatureEngineer(
        grid_df, preprocessor.poaching,
        preprocessor.roads, preprocessor.villages, preprocessor.water,
        preprocessor.rainfall, preprocessor.moon, preprocessor.ndvi
    )
    
    feature_engineer.compute_static_features()
    feature_engineer.aggregate_poaching_by_grid_week()
    feature_engineer.create_temporal_features()
    feature_engineer.add_target_variable()
    feature_engineer.add_lag_features()
    # Optionally add spatial-lag features and perform feature selection
    if use_spatial_lag:
        try:
            feature_engineer.add_spatial_lag_features(neighbor_distance=1, lags=[1])
        except Exception as e:
            print(f"Warning: spatial-lag addition failed: {e}")
    if use_feature_selection:
        try:
            feature_engineer.select_top_k_features(k=10)
        except Exception as e:
            print(f"Warning: feature selection failed: {e}")
    
    features_df = feature_engineer.get_features_dataframe()
    
    print(f"\n[OK] Feature Matrix Shape: {features_df.shape}")
    print(f"[OK] Target Distribution:\n{features_df['target'].value_counts()}")
    print(f"[OK] Feature Names: {list(features_df.columns)}")
    
    # ===== STEP 5: Model Training =====
    print(f"\n{'='*70}")
    print("STEP 5: Training Models (RF + XGBoost)")
    print(f"{'='*70}\n")
    
    trainer = PoachedModelTrainer(features_df)
    trainer.train_all()
    
    # ===== STEP 6: Evaluation =====
    print(f"\n{'='*70}")
    print("STEP 6: Model Evaluation")
    print(f"{'='*70}\n")
    
    metrics = trainer.evaluate()
    
    # ===== STEP 7: Save Models =====
    print(f"\n{'='*70}")
    print("STEP 7: Saving Models")
    print(f"{'='*70}\n")
    
    models_dir = Path('models')
    trainer.save_models(str(models_dir))
    
    # Save metrics
    with open(models_dir / 'evaluation_metrics.json', 'w') as f:
        import json
        # Convert numpy types to native Python types
        metrics_json = {
            'auc_score': float(metrics['auc_score']),
            'confusion_matrix': metrics['confusion_matrix'],
            'classification_report': metrics['classification_report'],
            'threshold': metrics['threshold']
        }
        json.dump(metrics_json, f, indent=2)
    
    # ===== STEP 8: Visualization =====
    print(f"\n{'='*70}")
    print("STEP 8: Creating Visualizations")
    print(f"{'='*70}\n")
    
    # Debug: Check grid_df state
    print(f"[DEBUG] grid_df shape before visualization: {grid_df.shape}")
    print(f"[DEBUG] Unique grid_ids in grid_df: {len(grid_df['grid_id'].unique())}")
    regions_in_grid = set(gid.split('_')[0] for gid in grid_df['grid_id'])
    print(f"[DEBUG] Regions in grid_df: {sorted(regions_in_grid)}")
    
    # Create predictions dataframe for ALL samples (not just test) to show all grid cells
    # This ensures all 967 grid cells appear in the output map
    X_all = features_df.drop(columns=['target', 'grid_id', 'week_start'], errors='ignore')
    X_all = X_all.fillna(X_all.mean(numeric_only=True))
    X_all = X_all.select_dtypes(include=[np.number])
    X_all_scaled = trainer.scaler.transform(X_all)
    
    # Get ensemble predictions for all data (average of RF and XGBoost)
    rf_preds_all = trainer.rf_model.predict_proba(X_all_scaled)[:, 1]
    xgb_preds_all = trainer.xgb_model.predict_proba(X_all_scaled)[:, 1]
    all_ensemble_preds = (rf_preds_all + xgb_preds_all) / 2.0
    
    predictions_df = features_df[['grid_id', 'week_start']].copy()
    predictions_df['predicted_probability'] = all_ensemble_preds
    predictions_df['actual'] = features_df['target'].values

    visualizer = PoachedVisualizer(grid_df, predictions_df, metrics)
    
    # Create GIS heatmap
    visualizer.create_heatmap_geojson('outputs/risk_heatmap.geojson')
    visualizer.create_folium_map('outputs/risk_map.html')
    
    # Create plots
    visualizer.plot_confusion_matrix(trainer.y_test, (trainer.ensemble_preds_test > 0.5).astype(int))
    
    # Feature importance
    rf_imp, xgb_imp = trainer.get_feature_importance()
    visualizer.plot_feature_importance(rf_imp, xgb_imp)
    
    # Patrol priority zones
    patrol_zones = visualizer.create_patrol_priority_zones()
    # Generate patrol routes GeoJSON
    visualizer.create_patrol_routes(top_n=15)
    
    # ===== FINAL SUMMARY =====
    print(f"\n{'='*70}")
    print(" PIPELINE COMPLETE - SUMMARY OF DELIVERABLES")
    print(f"{'='*70}")
    print(f"\n[DIR] Output Directory: outputs/")
    print(f"\n[FILES] Generated Files:")
    print(f"  - risk_heatmap.geojson - GIS-ready grid with risk probabilities")
    print(f"  - risk_map.html - Interactive Leaflet map (open in browser)")
    print(f"  - confusion_matrix.png - Model evaluation visualization")
    print(f"  - feature_importance.png - Feature importance comparison")
    print(f"  - patrol_priority_zones.csv - Top 15 high-risk cells for patrol")
    print(f"\n[MODELS] Models Saved:")
    print(f"  - models/random_forest_model.pkl")
    print(f"  - models/xgboost_model.pkl")
    print(f"  - models/scaler.pkl")
    print(f"  - models/evaluation_metrics.json")
    print(f"\n[METRICS] Key Metrics:")
    print(f"  - Ensemble AUC Score: {metrics['auc_score']:.4f}")
    print(f"  - Confusion Matrix:\n{np.array(metrics['confusion_matrix'])}")
    print(f"\n[NEXT] Next Steps:")
    print(f"  1. Open outputs/risk_map.html in your web browser")
    print(f"  2. Review patrol_priority_zones.csv for patrol planning")
    print(f"  3. Use trained models for weekly predictions on new data")
    print(f"\n" + f"{'='*70}\n")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run Poaching Activity Prediction pipeline')
    parser.add_argument('--no-spatial-lag', dest='no_spatial', action='store_true', help='Disable spatial-lag feature generation')
    parser.add_argument('--no-selection', dest='no_selection', action='store_true', help='Disable feature selection')
    args = parser.parse_args()

    try:
        main(use_spatial_lag=not args.no_spatial, use_feature_selection=not args.no_selection)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
