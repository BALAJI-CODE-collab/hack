"""Complete preprocessing pipeline for poaching prediction."""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.prepared import prep


def load_poaching_incidents(path):
    """Load poaching incidents CSV and create point geometries."""
    df = pd.read_csv(path, parse_dates=['date'])
    df['geometry'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
    return df


def load_geojson(path):
    """Load GeoJSON and return features with geometries."""
    with open(path, 'r') as f:
        fc = json.load(f)
    
    features = []
    for feat in fc.get('features', []):
        geom = shape(feat['geometry'])
        props = feat.get('properties', {})
        props['geometry'] = geom
        features.append(props)
    
    return features


def load_park_boundary(path):
    """Load park boundary and return as shapely geometry (supports multiple regions)."""
    from shapely.geometry import MultiPolygon
    features = load_geojson(path)
    if not features:
        raise ValueError(f"No features in {path}")
    
    geoms = [f['geometry'] for f in features]
    
    if len(geoms) == 1:
        return geoms[0]
    else:
        # Return MultiPolygon for multiple regions
        return MultiPolygon(geoms)


def load_roads(path):
    """Load roads and return list of LineString geometries."""
    features = load_geojson(path)
    return [f['geometry'] for f in features]


def load_villages(path):
    """Load villages and return list of Point geometries."""
    features = load_geojson(path)
    return [f['geometry'] for f in features]


def load_water(path):
    """Load water bodies and return list of geometries."""
    features = load_geojson(path)
    return [f['geometry'] for f in features]


def load_rainfall(path):
    """Load rainfall time series."""
    df = pd.read_csv(path, parse_dates=['week_start'])
    return df


def load_moon_phases(path):
    """Load moon phase data."""
    df = pd.read_csv(path, parse_dates=['date'])
    return df


def load_ndvi(path):
    """Load NDVI raster data.

    Loads a CSV from `path`, builds a `geometry` column from `lon` and `lat`
    using `Point(lon, lat)` and returns the DataFrame.
    """
    df = pd.read_csv(path)
    # Ensure required columns exist
    if 'lon' not in df.columns or 'lat' not in df.columns:
        raise KeyError(f"NDVI CSV at {path} must contain 'lon' and 'lat' columns")
    df['geometry'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
    return df


class DataPreprocessor:
    """Main data preprocessing coordinator."""
    
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.park_boundary = None
        self.roads = None
        self.villages = None
        self.water = None
        self.poaching = None
        self.rainfall = None
        self.moon = None
        self.ndvi = None
    
    def load_all(self):
        """Load all datasets."""
        print("Loading datasets...")
        self.park_boundary = load_park_boundary(self.data_dir / 'park_boundary.geojson')
        self.roads = load_roads(self.data_dir / 'roads.geojson')
        self.villages = load_villages(self.data_dir / 'villages.geojson')
        self.water = load_water(self.data_dir / 'water.geojson')
        self.poaching = load_poaching_incidents(self.data_dir / 'poaching_incidents.csv')
        self.rainfall = load_rainfall(self.data_dir / 'rainfall.csv')
        self.moon = load_moon_phases(self.data_dir / 'moon_phases.csv')
        self.ndvi = load_ndvi(self.data_dir / 'ndvi.csv')
        print(f"✓ Loaded {len(self.poaching)} poaching incidents")
        print(f"✓ Park area: {self.park_boundary.bounds}")
    
    def clip_to_park(self):
        """Clip poaching incidents to park boundary."""
        park_prep = prep(self.park_boundary)
        mask = self.poaching['geometry'].apply(lambda geom: park_prep.contains(geom))
        self.poaching = self.poaching[mask].reset_index(drop=True)
        print(f"✓ Clipped to park: {len(self.poaching)} incidents")
    
    def validate_data(self):
        """Validate loaded data."""
        assert self.poaching is not None and len(self.poaching) > 0, "No poaching data"
        assert self.park_boundary is not None, "No park boundary"
        print("✓ Data validation passed")
    
    def get_summary(self):
        """Print dataset summary."""
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        print(f"Poaching incidents: {len(self.poaching)}")
        print(f"Date range: {self.poaching['date'].min()} to {self.poaching['date'].max()}")
        print(f"Roads: {len(self.roads)}")
        print(f"Villages: {len(self.villages)}")
        print(f"Water bodies: {len(self.water)}")
        print(f"NDVI samples: {len(self.ndvi)}")
        print("="*60 + "\n")


if __name__ == '__main__':
    preprocessor = DataPreprocessor()
    preprocessor.load_all()
    preprocessor.validate_data()
    preprocessor.clip_to_park()
    preprocessor.get_summary()
