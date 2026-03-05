import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points

def compute_distance_to_nearest(grid_df, target_geoms, col_name):
    # grid_df: DataFrame with 'geometry' (shapely polygons)
    # target_geoms: list of shapely geometries
    from shapely.ops import nearest_points
    targ_union = None
    try:
        # create a simple list union if many
        from shapely.ops import unary_union
        targ_union = unary_union(target_geoms)
    except Exception:
        targ_union = target_geoms[0] if target_geoms else None
    dists = []
    for geom in grid_df['geometry']:
        cent = geom.centroid
        if targ_union is None:
            dists.append(np.nan)
        else:
            near = nearest_points(cent, targ_union)[1]
            dists.append(cent.distance(near))
    grid_df[col_name] = dists
    return grid_df

def mean_ndvi_per_grid(grid_df, seed=0):
    # Generate a reproducible pseudo-NDVI value per grid cell based on centroid
    rng = np.random.default_rng(seed)
    vals = []
    for geom in grid_df['geometry']:
        cent = geom.centroid
        # use centroid coords to seed a deterministic value
        val = 0.4 + 0.2 * np.sin(cent.x * 10) + 0.1 * np.cos(cent.y * 12)
        val += rng.normal(0, 0.05)
        vals.append(float(np.clip(val, -1, 1)))
    grid_df['mean_ndvi'] = vals
    return grid_df

def add_weekly_dynamic_features(weekly_df, rainfall_df, moon_df):
    wf = weekly_df.merge(rainfall_df, on='week_start', how='left')
    wf = wf.merge(moon_df, left_on='week_start', right_on='date', how='left')
    return wf

def add_lag_feature(weekly_df, lag_weeks=1):
    weekly_df = weekly_df.sort_values(['grid_id','week_start'])
    weekly_df['poaching_lag'] = weekly_df.groupby('grid_id')['poaching_count'].shift(lag_weeks).fillna(0)
    return weekly_df
