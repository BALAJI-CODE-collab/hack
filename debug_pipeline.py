#!/usr/bin/env python3
"""Debug why pipeline only creates 100 cells instead of 967."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing import DataPreprocessor
from preprocessing.grid import create_grid, FOREST_REGIONS

# Generate data
from data.generate_sample_data import (
    generate_park_boundary, generate_roads, generate_villages, 
    generate_water, generate_poaching_incidents, generate_rainfall,  
    generate_moon_phases, generate_ndvi
)

data_dir = Path('data')
print("=" * 70)
print("STEP 1: Generate Sample Data")
print("=" * 70)

park = generate_park_boundary(data_dir / 'park_boundary.geojson')
generate_roads(data_dir / 'roads.geojson', park, num_roads=5)
generate_villages(data_dir / 'villages.geojson', park, num_villages=8)
generate_water(data_dir / 'water.geojson', park, num_waterbodies=4)
generate_poaching_incidents(data_dir / 'poaching_incidents.csv', park, num_incidents=150)
generate_rainfall(data_dir / 'rainfall.csv')
generate_moon_phases(data_dir / 'moon_phases.csv')
generate_ndvi(data_dir / 'ndvi.csv', park)

print("\n" + "=" * 70)
print("STEP 2: Load Data with Preprocessor")
print("=" * 70)

preprocessor = DataPreprocessor(str(data_dir))
preprocessor.load_all()
print(f"\npark_boundary type: {type(preprocessor.park_boundary)}")
print(f"park_boundary geom_type: {preprocessor.park_boundary.geom_type if hasattr(preprocessor.park_boundary, 'geom_type') else 'N/A'}")
print(f"park_boundary bounds: {preprocessor.park_boundary.bounds}")

print("\n" + "=" * 70)
print("STEP 3: Check FOREST_REGIONS")
print("=" * 70)

print(f"\nFOREST_REGIONS defined: {len(FOREST_REGIONS)} regions")
for i, region in enumerate(FOREST_REGIONS):
    print(f"  Region {i}: {region['name']} - {region['bounds']}")

print("\n" + "=" * 70)
print("STEP 4: Create Grid")
print("=" * 70)

grid_df = create_grid(preprocessor.park_boundary, cell_size_deg=0.3)
print(f"\n✓ Grid created with {len(grid_df)} cells")

# Check regions in grid
regions_in_grid = set(gid.split('_')[0] for gid in grid_df['grid_id'])
print(f"  Regions found: {sorted(regions_in_grid)}")

# Count per region
from collections import Counter
region_counts = Counter(gid.split('_')[0] for gid in grid_df['grid_id'])
for region_idx in sorted(region_counts.keys()):
    region_name = FOREST_REGIONS[int(region_idx)]['name']
    print(f"  Region {region_idx} ({region_name}): {region_counts[region_idx]} cells")

print("\nDone!")
