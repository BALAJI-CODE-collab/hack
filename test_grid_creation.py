import sys
sys.path.insert(0, '/c/Project')
from preprocessing.grid import create_grid, FOREST_REGIONS
from preprocessing import DataPreprocessor

# Load the park boundary
preprocessor = DataPreprocessor()
park = preprocessor.park_boundary

print(f"Park geometry type: {park.geom_type}")
print(f"Park bounds: {park.bounds}")

# Create grid
grid = create_grid(park, cell_size_deg=0.3)

print(f"\nTotal grid cells created: {len(grid)}")

# Check regions in grid
regions_found = set()
for grid_id in grid['grid_id'].unique():
    region_idx = grid_id.split('_')[0]
    regions_found.add(region_idx)

print(f"Regions in grid: {sorted(regions_found)}")

# Count by region
for region_idx in sorted(regions_found):
    count = len(grid[grid['grid_id'].str.startswith(region_idx + '_')])
    if region_idx in ['0', '1', '2', '3']:
        print(f"  Region {region_idx} ({FOREST_REGIONS[int(region_idx)]['name']}): {count} cells")
