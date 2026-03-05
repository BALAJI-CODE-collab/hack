import sys
sys.path.insert(0, '/c/Project')

from preprocessing import DataPreprocessor
from preprocessing.grid import create_grid, FOREST_REGIONS

preprocessor = DataPreprocessor()
preprocessor.load_all()

print(f"Park boundary: {preprocessor.park_boundary.geom_type}")
print(f"Number of geometries: {len(list(preprocessor.park_boundary.geoms))}")

grid = create_grid(preprocessor.park_boundary, cell_size_deg=0.3)

print(f"\nTotal grid cells created: {len(grid)}")

# Check regions in grid
regions_found = set()
region_counts = {}

for grid_id in grid['grid_id']:
    region_idx = grid_id.split('_')[0]
    regions_found.add(region_idx)
    region_counts[region_idx] = region_counts.get(region_idx, 0) + 1

print(f"Regions in grid: {sorted(regions_found)}")
print("\nCells per region:")
for r in sorted(region_counts.keys()):
    if r in ['0', '1', '2', '3']:
        region_name = FOREST_REGIONS[int(r)]['name']
        print(f"  Region {r} ({region_name}): {region_counts[r]} cells")
