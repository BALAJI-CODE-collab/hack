#!/usr/bin/env python3
"""Test to find where cells get dropped."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from data.generate_sample_data import (
    generate_park_boundary, generate_roads, generate_villages, 
    generate_water, generate_poaching_incidents, generate_rainfall,  
    generate_moon_phases, generate_ndvi
)
from preprocessing import DataPreprocessor
from preprocessing.grid import create_grid, assign_points_to_grid
from feature_engineering import FeatureEngineer

data_dir = Path('data')

# Generate data
print("Generating data...")
park = generate_park_boundary(data_dir / 'park_boundary.geojson')
generate_roads(data_dir / 'roads.geojson', park, num_roads=5)
generate_villages(data_dir / 'villages.geojson', park, num_villages=8)
generate_water(data_dir / 'water.geojson', park, num_waterbodies=4)
generate_poaching_incidents(data_dir / 'poaching_incidents.csv', park, num_incidents=150)
generate_rainfall(data_dir / 'rainfall.csv')
generate_moon_phases(data_dir / 'moon_phases.csv')
generate_ndvi(data_dir / 'ndvi.csv', park)

# Load data
print("Loading data...")
preprocessor = DataPreprocessor(str(data_dir))
preprocessor.load_all()
preprocessor.clip_to_park()

# Create grid
print("Creating grid...")
grid_df = create_grid(preprocessor.park_boundary, cell_size_deg=0.3)
print(f"  Grid cells after create_grid: {len(grid_df)}")

# Assign points
poaching_with_grid = assign_points_to_grid(preprocessor.poaching, grid_df)
print(f"  Incidents assigned to grid: {len(poaching_with_grid[poaching_with_grid['grid_id'].notna()])}")

# Feature engineering
print("Creating features...")
feature_engineer = FeatureEngineer(
    grid_df, poaching_with_grid,
    preprocessor.roads, preprocessor.villages, preprocessor.water,
    preprocessor.rainfall, preprocessor.moon, preprocessor.ndvi
)

print(f"\nBefore feature engineering:")
print(f"  Grid DF has {len(feature_engineer.grid_df)} rows")
print(f"  Unique grid_ids: {feature_engineer.grid_df['grid_id'].nunique()}")

feature_engineer.compute_static_features()
print(f"\nAfter compute_static_features:")
print(f"  Static features: {len(feature_engineer.static_features)} rows")

feature_engineer.aggregate_poaching_by_grid_week()
print(f"\nAfter aggregate_poaching_by_grid_week:")
print(f"  Features_df: {len(feature_engineer.features_df)} rows")
print(f"  Unique grid_ids in features_df: {feature_engineer.features_df['grid_id'].nunique()}")

# Show which grid_ids are in features_df
grid_ids_in_features = feature_engineer.features_df['grid_id'].unique()
print(f"\n  Sample grid_ids: {list(grid_ids_in_features[:5])}")

# Check regions
region_counts = {}
for gid in grid_ids_in_features:
    region = gid.split('_')[0]
    region_counts[region] = region_counts.get(region, 0) + 1

print(f"\n  Grid cells per region in features_df:")
for rid in sorted(region_counts.keys()):
    print(f"    Region {rid}: {region_counts[rid]} cells")
