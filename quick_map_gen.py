#!/usr/bin/env python
"""Quick map regeneration with visual hotspots"""
import pandas as pd
import numpy as np
from pathlib import Path
from visualization import PoachedVisualizer

# Load existing predictions
try:
    predictions_df = pd.read_csv('outputs/sample_predictions.csv')
    grid_df = None
    
    # Try to load grid from sample data or create synthetic
    try:
        import geopandas as gpd
        from preprocessing.grid import create_grid
        
        # Load or create grid
        park_boundary = None
        try:
            import json
            with open('data/park_boundary.geojson') as f:
                data = json.load(f)
                if data['features']:
                    from shapely.geometry import shape
                    park_boundary = shape(data['features'][0]['geometry'])
        except:
            pass
        
        if park_boundary:
            grid_df = create_grid(park_boundary, cell_size_deg=0.3)
        else:
            # Create synthetic grid
            from shapely.geometry import box
            polys = []
            ids = []
            regions = [
                {'name': 'Serengeti', 'bounds': (33.0, -3.0, 36.0, 0.0)},
                {'name': 'Amazon', 'bounds': (-75.0, -5.0, -70.0, 0.0)},
                {'name': 'Congo', 'bounds': (15.0, -5.0, 20.0, 0.0)},
                {'name': 'SE_Asia', 'bounds': (105.0, 5.0, 110.0, 10.0)}
            ]
            
            cell_size = 0.3
            for region_idx, region in enumerate(regions):
                minx, miny, maxx, maxy = region['bounds']
                x_coords = np.arange(minx, maxx, cell_size)
                y_coords = np.arange(miny, maxy, cell_size)
                
                for i, x in enumerate(x_coords):
                    for j, y in enumerate(y_coords):
                        poly = box(x, y, x+cell_size, y+cell_size)
                        polys.append(poly)
                        ids.append(f"{region_idx}_{i}_{j}_{region['name']}")
            
            grid_df = pd.DataFrame({'grid_id': ids, 'geometry': polys})
    except Exception as e:
        print(f"Error loading grid: {e}")
        import traceback
        traceback.print_exc()
    
    if grid_df is not None:
        # Create visualizer with dummy metrics
        visualizer = PoachedVisualizer(
            grid_df=grid_df,
            predictions_df=predictions_df,
            metrics={'confusion_matrix': [[0, 0], [0, 0]]}
        )
        
        # Generate map with hotspots
        visualizer.create_folium_map('outputs/risk_map.html', show_forest_regions=True)
        print("✅ Map regenerated with high-risk hotspots!")
        print("   - Red zones: Top 25% (Very High Risk)")
        print("   - Orange zones: 50-75% (High Risk)")
        print("   - Yellow zones: 25-50% (Medium Risk)")
        print("   - Light Blue zones: Bottom 25% (Low Risk)")
        print("\n✓ Open outputs/risk_map.html to view")
    else:
        print("❌ Could not create grid")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
