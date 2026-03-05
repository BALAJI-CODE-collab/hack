"""Main pipeline to run the end-to-end workflow.
Run `python main.py` to execute using sample data (generated if missing).
"""
from pathlib import Path
import os
import pandas as pd
from shapely.geometry import shape
from preprocessing import load_data
from preprocessing.grid import create_grid, assign_points_to_grid
from feature_engineering.features import compute_distance_to_nearest, mean_ndvi_per_grid, add_lag_feature
from models.train import prepare_data, train_models
from visualization.visualize import create_heatmap, highlight_top_grids, make_simple_patrol_routes

# ===== CONFIG: Update these paths to point to your datasets =====
DATA_CONFIG = {
    'park_boundary': 'data/your_data/park_boundary.geojson',
    'roads': 'data/your_data/roads.geojson',
    'villages': 'data/your_data/villages.geojson',
    'water': 'data/your_data/water.geojson',
    'poaching_incidents': 'data/your_data/poaching_incidents.csv',
    'rainfall': 'data/your_data/rainfall.csv',
    'moon_phases': 'data/your_data/moon_phases.csv',
}
# ===== END CONFIG =====

def run():
    # Load user-provided datasets
    print("Loading datasets from configured paths...")
    try:
        park_list = load_data.load_geojson_geoms(DATA_CONFIG['park_boundary'])
        park_geom = park_list[0][0]
        roads = [g for g, p in load_data.load_geojson_geoms(DATA_CONFIG['roads'])]
        villages = [g for g, p in load_data.load_geojson_geoms(DATA_CONFIG['villages'])]
        water = [g for g, p in load_data.load_geojson_geoms(DATA_CONFIG['water'])]
        incidents = load_data.load_poaching(DATA_CONFIG['poaching_incidents'])
        rainfall_df = pd.read_csv(DATA_CONFIG['rainfall'], parse_dates=['week_start'])
        moon_df = pd.read_csv(DATA_CONFIG['moon_phases'], parse_dates=['date'])
        print("✓ All datasets loaded successfully")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("Please update DATA_CONFIG in main.py with paths to your real datasets.")
        return

    # create grid (use ~0.01 deg ~ ~1km cell for small park)
    grid = create_grid(park_geom, cell_size_deg=0.3)  # ~30km cells for larger park

    # assign incidents to grid and aggregate weekly
    assigned = assign_points_to_grid(incidents, grid)
    assigned['week_start'] = assigned['date'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly = assigned.groupby(['grid_id','week_start']).size().reset_index(name='poaching_count')

    # ensure all grid-week combos present
    weeks = pd.date_range(start='2020-01-01', periods=52, freq='W-MON')
    base = pd.MultiIndex.from_product([grid['grid_id'], weeks], names=['grid_id','week_start']).to_frame(index=False)
    weekly_full = base.merge(weekly, on=['grid_id','week_start'], how='left').fillna({'poaching_count':0})

    # add static features
    grid = compute_distance_to_nearest(grid, roads, 'dist_road')
    grid = compute_distance_to_nearest(grid, villages, 'dist_village')
    grid = compute_distance_to_nearest(grid, water, 'dist_water')
    grid = mean_ndvi_per_grid(grid, seed=0)

    # merge static features into weekly
    weekly_full = weekly_full.merge(grid[['grid_id','dist_road','dist_village','dist_water','mean_ndvi']], on='grid_id', how='left')

    # label
    weekly_full['target'] = (weekly_full['poaching_count'] > 0).astype(int)

    # lag
    weekly_full = add_lag_feature(weekly_full, lag_weeks=1)

    # features & train
    feature_cols = ['dist_road','dist_village','dist_water','mean_ndvi','poaching_lag']
    X, y = prepare_data(weekly_full, feature_cols, target_col='target')

    os.makedirs('models', exist_ok=True)
    res = train_models(X, y)
    print(f"Ensemble AUC: {res['auc']:.3f}")

    # attach probabilities back to grid-week and visualize
    rf = res['rf']
    xgb = res['xgb']
    weekly_full['risk_proba'] = (rf.predict_proba(X)[:,1] + xgb.predict_proba(X)[:,1]) / 2.0

    # aggregate risk per grid (mean over recent weeks)
    grid_risk = weekly_full.groupby('grid_id')['risk_proba'].mean().reset_index()
    grid_out = grid.merge(grid_risk, on='grid_id', how='left')
    grid_out['risk_proba'] = grid_out['risk_proba'].fillna(0)

    os.makedirs('outputs', exist_ok=True)
    create_heatmap(grid_out, prob_col='risk_proba', park_geom=park_geom, out_html='outputs/heatmap.html')
    highlight_top_grids(grid_out, top_n=15, out_html='outputs/top_grids.html')
    make_simple_patrol_routes(grid_out, top_n=15, out_html='outputs/patrol_routes.html')

if __name__ == '__main__':
    run()
