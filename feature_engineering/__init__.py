"""Feature engineering for poaching prediction."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class FeatureEngineer:
    def __init__(self, grid_df, poaching_df, roads_list, villages_list, water_list, rainfall_df, moon_df, ndvi_df):
        """Initialize feature engineer with all datasets."""
        self.grid_df = grid_df
        self.poaching_df = poaching_df.copy() if hasattr(poaching_df, 'copy') else poaching_df
        self.roads_list = roads_list  # List of geometries
        self.villages_list = villages_list  # List of geometries
        self.water_list = water_list  # List of geometries
        self.rainfall_df = rainfall_df
        self.moon_df = moon_df
        self.ndvi_df = ndvi_df
        self.features_df = None
    
    def compute_static_features(self):
        """Compute static features: distance to roads/villages/water, mean NDVI per grid."""
        print("Computing static features...")
        
        static_features = []
        for _, grid_row in self.grid_df.iterrows():
            grid_geom = grid_row['geometry']
            grid_id = grid_row['grid_id']
            
            # Distance to nearest road
            dist_to_road = min([grid_geom.distance(road) for road in self.roads_list]) if len(self.roads_list) > 0 else 0
            
            # Distance to nearest village
            dist_to_village = min([grid_geom.distance(vill) for vill in self.villages_list]) if len(self.villages_list) > 0 else 0
            
            # Distance to nearest water body
            dist_to_water = min([grid_geom.distance(water) for water in self.water_list]) if len(self.water_list) > 0 else 0
            
            # Mean NDVI in grid cell
            ndvi_in_grid = self.ndvi_df[self.ndvi_df['geometry'].apply(lambda p: grid_geom.contains(p))]
            mean_ndvi = ndvi_in_grid['ndvi'].mean() if len(ndvi_in_grid) > 0 else 0
            
            static_features.append({
                'grid_id': grid_id,
                'dist_to_road_km': dist_to_road * 111,
                'dist_to_village_km': dist_to_village * 111,
                'dist_to_water_km':dist_to_water * 111,
                'mean_ndvi': mean_ndvi
            })
        
        self.static_features = pd.DataFrame(static_features)
        print(f"? Static features computed for {len(self.static_features)} grid cells")
    
    def aggregate_poaching_by_grid_week(self):
        """Aggregate poaching counts by grid cell and week."""
        print("Aggregating poaching by grid-week...")
        
        min_date = pd.Timestamp(self.poaching_df['date'].min())
        max_date = pd.Timestamp(self.poaching_df['date'].max())
        weeks = pd.date_range(min_date, max_date, freq='W')
        
        grid_week_data = []
        for grid_id in self.grid_df['grid_id'].unique():
            for week_start in weeks:
                grid_week_data.append({
                    'grid_id': grid_id,
                    'week_start': week_start,
                })
        
        self.features_df = pd.DataFrame(grid_week_data)
        print(f"? Aggregated into {len(self.features_df)} grid-week combinations")
    
    def create_temporal_features(self):
        """Create temporal features: rainfall, moon phase, season."""
        print("Creating temporal features...")
        
        for idx, row in self.features_df.iterrows():
            week_start = pd.Timestamp(row['week_start'])
            
            rainfall_data = self.rainfall_df[self.rainfall_df['week_start'] == week_start.strftime('%Y-%m-%d')]
            rainfall = rainfall_data['rainfall_mm'].values[0] if len(rainfall_data) > 0 else 0
            
            moon_data = self.moon_df[self.moon_df['date'] == week_start.strftime('%Y-%m-%d')]
            moon_illumination = moon_data['illumination'].values[0] if len(moon_data) > 0 else 0.5
            
            day_of_year = week_start.dayofyear
            season = 'Dry' if day_of_year > 182 else 'Wet'
            
            self.features_df.at[idx, 'rainfall_mm'] = rainfall
            self.features_df.at[idx, 'moon_illumination'] = moon_illumination
            self.features_df.at[idx, 'season'] = season
            self.features_df.at[idx, 'day_of_year'] = day_of_year
        
        print(f"? Created {len(self.features_df)} temporal feature rows")
    
    def add_target_variable(self):
        """Create binary target: 1 if poaching occurred in grid-week, 0 otherwise."""
        print("Creating target variable...")
        
        targets = []
        for _, row in self.features_df.iterrows():
            grid_id = row['grid_id']
            week_start = pd.Timestamp(row['week_start'])
            week_end = week_start + pd.Timedelta(days=7)
            
            relevant_incidents = self.poaching_df[
                (self.poaching_df.get('grid_id') == grid_id) &
                (self.poaching_df['date'] >= week_start) &
                (self.poaching_df['date'] < week_end)
            ]
            
            targets.append(1 if len(relevant_incidents) > 0 else 0)
        
        self.features_df['target'] = targets
        print(f"? Target variable created ({self.features_df['target'].sum()} positive cases)")
    
    def add_lag_features(self):
        """Add lag features (previous week's poaching count)."""
        print("Adding lag features...")
        
        self.features_df['poaching_count_lag1'] = 0
        
        for grid_id in self.features_df['grid_id'].unique():
            grid_data = self.features_df[self.features_df['grid_id'] == grid_id].sort_values('week_start')
            self.features_df.loc[grid_data.index, 'poaching_count_lag1'] = grid_data['target'].shift(1).fillna(0).values
        
        print("? Lag features added")

    def add_spatial_lag_features(self, neighbor_distance=1, lags=[1]):
        """Add spatial lag features: average poaching in neighboring cells for previous weeks.

        neighbor_distance: Manhattan distance in grid coordinates to consider neighbors.
        lags: list of integer week lags to compute (1 => previous week)
        """
        print("Adding spatial-lag features...")

        # build neighbor index from grid ids
        def to_coords(gid):
            i, j = gid.split('_')
            return int(i), int(j)

        coords = {gid: to_coords(gid) for gid in self.grid_df['grid_id'].unique()}

        # precompute neighbors for each grid_id
        neighbors = {}
        for gid, (i, j) in coords.items():
            neigh = []
            for ogid, (oi, oj) in coords.items():
                if abs(oi - i) + abs(oj - j) <= neighbor_distance and ogid != gid:
                    neigh.append(ogid)
            neighbors[gid] = neigh

        # ensure week_start is Timestamp
        self.features_df['week_start'] = pd.to_datetime(self.features_df['week_start'])

        for lag in lags:
            col = f'spatial_lag_mean_lag{lag}'
            vals = []
            for _, row in self.features_df.iterrows():
                gid = row['grid_id']
                wk = pd.Timestamp(row['week_start']) - pd.Timedelta(days=7*lag)
                neigh_ids = neighbors.get(gid, [])
                if not neigh_ids:
                    vals.append(0)
                    continue
                mask = (self.features_df['grid_id'].isin(neigh_ids)) & (self.features_df['week_start'] == wk)
                neigh_rows = self.features_df.loc[mask]
                if len(neigh_rows) == 0:
                    vals.append(0)
                else:
                    vals.append(neigh_rows['target'].mean())
            self.features_df[col] = vals

        print("✓ Spatial-lag features added")

    def select_top_k_features(self, k=10):
        """Select top-k numeric features by mutual information with the target.

        This reduces the feature matrix to the most informative numeric features.
        """
        print(f"Selecting top {k} features by mutual information...")
        from sklearn.feature_selection import mutual_info_classif

        numeric = self.features_df.select_dtypes(include=[np.number]).copy()
        if 'target' not in numeric.columns:
            print("No numeric target found; skipping feature selection")
            self.selected_features = list(self.features_df.columns)
            return

        Xnum = numeric.drop(columns=['target'], errors='ignore')
        y = numeric['target']
        if Xnum.shape[1] == 0:
            self.selected_features = []
            print("No numeric features to select")
            return

        mi = mutual_info_classif(Xnum.fillna(0), y, random_state=42)
        mi_series = pd.Series(mi, index=Xnum.columns).sort_values(ascending=False)
        topk = list(mi_series.iloc[:k].index)

        # always keep target, grid_id, week_start
        self.selected_features = ['grid_id', 'week_start', 'target'] + topk
        print(f"✓ Selected features: {topk}")
        # reduce features_df (keep selected and any spatial lag columns)
        keep = [c for c in self.features_df.columns if c in self.selected_features or c.startswith('spatial_lag')]
        self.features_df = self.features_df[keep]
    
    def get_features_dataframe(self):
        """Get final features dataframe."""
        return self.features_df.copy() if self.features_df is not None else None


if __name__ == '__main__':
    print("Feature engineering module ready to use")
