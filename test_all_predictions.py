#!/usr/bin/env python3
"""Test predictions for all grid cells."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing import DataPreprocessor
from preprocessing.grid import create_grid
from feature_engineering import FeatureEngineer
from data.generate_sample_data import *

# Generate data
print("Generating data...")
data_dir = Path('data')
generate_park_boundary(data_dir / 'park_boundary.geojson')
generate_roads(data_dir / 'roads.geojson', None)
generate_villages(data_dir / 'villages.geojson', None)
generate_water(data_dir / 'water.geojson', None)
generate_poaching_incidents(data_dir / 'poaching_incidents.csv', None)
generate_rainfall(data_dir / 'rainfall.csv')
generate_moon_phases(data_dir / 'moon_phases.csv')
generate_ndvi(data_dir / 'ndvi.csv', None)

# Load and preprocess
print("Loading data...")
preprocessor = DataPreprocessor(str(data_dir))
preprocessor.load_all()
preprocessor.clip_to_park()

# Create grid
print("Creating grid...")
grid_df = create_grid(preprocessor.park_boundary, cell_size_deg=0.3)
print(f"  Total grid cells: {len(grid_df)}")
regions = set(gid.split('_')[0] for gid in grid_df['grid_id'])
print(f"  Regions: {sorted(regions)}")

# Assign poaching incidents to grid
poaching_with_grid = assign_points_to_grid(preprocessor.poaching, grid_df)
preprocessor.poaching = poaching_with_grid

# Feature engineering
print("Engineering features...")
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

features_df = feature_engineer.get_features_dataframe()
print(f"  Features shape: {features_df.shape}")
print(f"  Unique grid cells: {len(features_df['grid_id'].unique())}")

# Check grid cells per region
region_counts = {}
for region_id in regions:
    count = len(features_df[features_df['grid_id'].str.startswith(region_id)])
    region_counts[region_id] = count
    print(f"  Region {region_id}: {count} grid-week records")

print("\nDONE - All 967 grid cells should be present in features_df!")
