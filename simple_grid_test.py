#!/usr/bin/env python3
"""Simple test of grid creation."""
from preprocessing.grid import create_grid, FOREST_REGIONS

print(f"FOREST_REGIONS has {len(FOREST_REGIONS)} regions")
grid = create_grid(None, cell_size_deg=0.3)
print(f"Grid created with {len(grid)} cells")

# Count per region
from collections import Counter
counts = Counter(gid.split('_')[0] for gid in grid['grid_id'])
for rid in sorted(counts.keys()):
    print(f"  Region {rid}: {counts[rid]} cells")
