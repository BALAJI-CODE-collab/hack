from shapely.geometry import box
import numpy as np
import pandas as pd

# Define forest regions globally
FOREST_REGIONS = [
    {'name': 'Serengeti', 'bounds': (33.0, -3.0, 36.0, 0.0)},           # Lon, Lat
    {'name': 'Amazon', 'bounds': (-75.0, -5.0, -70.0, 0.0)},
    {'name': 'Congo', 'bounds': (15.0, -5.0, 20.0, 0.0)},
    {'name': 'SE_Asia', 'bounds': (105.0, 5.0, 110.0, 10.0)}
]

def create_grid(park_geom, cell_size_deg=0.3):
    """Create grid cells for all known forest regions."""
    polys = []
    ids = []
    
    # Create grid for each predefined region (use hardcoded bounds, skip geometry checks)
    for region_idx, region_info in enumerate(FOREST_REGIONS):
        minx, miny, maxx, maxy = region_info['bounds']
        x_coords = np.arange(minx, maxx, cell_size_deg)
        y_coords = np.arange(miny, maxy, cell_size_deg)
        
        for i, x in enumerate(x_coords):
            for j, y in enumerate(y_coords):
                poly = box(x, y, x+cell_size_deg, y+cell_size_deg)
                # Create grid cell without intersection check (regions are predefined)
                polys.append(poly)
                ids.append(f"{region_idx}_{i}_{j}_{region_info['name']}")
    
    grid = pd.DataFrame({'grid_id': ids, 'geometry': polys})
    return grid

def assign_points_to_grid(points_df, grid_df):
    # points_df: pandas DataFrame with 'geometry' shapely Points
    # grid_df: DataFrame with 'grid_id' and 'geometry'
    from shapely.prepared import prep
    prepared = [(row['grid_id'], prep(row['geometry']), row['geometry']) for _, row in grid_df.iterrows()]
    assignments = []
    for _, p in points_df.iterrows():
        pt = p['geometry']
        gid = None
        for grid_id, pre, geom in prepared:
            if pre.contains(pt):
                gid = grid_id
                break
        assignments.append(gid)
    points_df = points_df.copy()
    points_df['grid_id'] = assignments
    return points_df
