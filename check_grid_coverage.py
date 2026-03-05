import json
import pandas as pd

# Check grid cells in output
with open('outputs/risk_heatmap.geojson') as f:
    geojson = json.load(f)
    
grid_ids = sorted([f['properties']['grid_id'] for f in geojson['features']])
print(f"Total grid cells: {len(grid_ids)}")
print(f"Grid cell IDs sample: {grid_ids[:10]} ... {grid_ids[-5:]}")

# Extract ranges
x_coords = sorted(set(int(g.split('_')[0]) for g in grid_ids))
y_coords = sorted(set(int(g.split('_')[1]) for g in grid_ids))
print(f"\nX range: {min(x_coords)} to {max(x_coords)} ({len(x_coords)} columns)")
print(f"Y range: {min(y_coords)} to {max(y_coords)} ({len(y_coords)} rows)")
print(f"Expected cells: {len(x_coords) * len(y_coords)}")
print(f"Actual cells: {len(grid_ids)}")

# Check which cells exist
expected_cells = {f"{i}_{j}" for i in x_coords for j in y_coords}
actual_cells = set(grid_ids)
missing_cells = expected_cells - actual_cells
print(f"\nMissing cells (not in region): {len(missing_cells)}")
if missing_cells:
    print(f"Examples: {list(missing_cells)[:5]}")
