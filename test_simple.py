#!/usr/bin/env python
import sys  
import traceback

sys.path.insert(0, '/c/Project')

try:
    from preprocessing import DataPreprocessor
    print("✓ Imports successful")
    
    preprocessor = DataPreprocessor()
    print("✓ DataPreprocessor created")
    
    park = preprocessor.park_boundary
    print(f"✓ Park loaded: {park.geom_type}")
    
    from preprocessing.grid import create_grid, FOREST_REGIONS
    print("✓ Grid module imported")
    
    grid = create_grid(park, cell_size_deg=0.3)
    print(f"✓ Grid created with {len(grid)} cells")
    
    regions_found = set(g.split('_')[0] for g in grid['grid_id'])
    print(f"✓ Regions found: {sorted(regions_found)}")
    
    for r in sorted(regions_found):
        count = sum(1 for g in grid['grid_id'] if g.split('_')[0] == r)
        print(f"  Region {r}: {count} cells")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
