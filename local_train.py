"""
ALTERNATIVE: Direct Data Loading + Training (Run locally if Colab fails)
Usage: python local_train.py
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from shapely.geometry import shape, Point, box
from shapely.prepared import prep
from shapely.ops import nearest_points, unary_union
import warnings
warnings.filterwarnings('ignore')

# ===== CONFIG: Update these paths =====
DATA_CONFIG = {
    'park_boundary': 'data/park_boundary.geojson',
    'roads': 'data/roads.geojson',
    'villages': 'data/villages.geojson',
    'water': 'data/water.geojson',
    'poaching_incidents': 'data/poaching_incidents.csv',
    'rainfall': 'data/rainfall.csv',
    'moon_phases': 'data/moon_phases.csv',
}
# =====================================

def load_geojson_geoms(path):
    """Load GeoJSON file and extract geometries."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            coll = json.load(f)
        res = []
        for feat in coll.get('features', []):
            geom = shape(feat['geometry'])
            props = feat.get('properties', {})
            res.append((geom, props))
        return res
    except Exception as e:
        print(f"✗ Failed to load {path}: {e}")
        return []

def load_poaching(path):
    """Load poaching incidents CSV."""
    try:
        df = pd.read_csv(path, parse_dates=['date'])
        # Ensure lon/lat columns exist
        if 'lon' not in df.columns or 'lat' not in df.columns:
            raise ValueError("CSV must have 'lon' and 'lat' columns")
        df['geometry'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
        return df
    except Exception as e:
        print(f"✗ Failed to load {path}: {e}")
        return pd.DataFrame()

def validate_data():
    """Check all files exist and are readable."""
    print("=" * 60)
    print("VALIDATING DATASETS")
    print("=" * 60)
    
    all_found = True
    for key, path in DATA_CONFIG.items():
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024*1024)
            print(f"✓ {key:20} {path} ({size_mb:.2f} MB)")
        else:
            print(f"✗ {key:20} NOT FOUND: {path}")
            all_found = False
    
    if not all_found:
        print("\n⚠ Some files missing! Check paths above.")
        print("Expected structure:")
        print("  project/")
        print("    data/")
        print("      park_boundary.geojson")
        print("      roads.geojson")
        print("      villages.geojson")
        print("      water.geojson")
        print("      poaching_incidents.csv")
        print("      rainfall.csv")
        print("      moon_phases.csv")
        return False
    
    return True

def main():
    # Validate files
    if not validate_data():
        print("\n✗ Cannot proceed. Fix missing files and try again.")
        return
    
    # Load data
    print("\n" + "=" * 60)
    print("LOADING DATASETS")
    print("=" * 60)
    
    park_list = load_geojson_geoms(DATA_CONFIG['park_boundary'])
    if not park_list:
        print("✗ Cannot load park boundary. Exiting.")
        return
    
    park_geom = park_list[0][0]
    roads = [g for g, p in load_geojson_geoms(DATA_CONFIG['roads'])]
    villages = [g for g, p in load_geojson_geoms(DATA_CONFIG['villages'])]
    water = [g for g, p in load_geojson_geoms(DATA_CONFIG['water'])]
    
    incidents = load_poaching(DATA_CONFIG['poaching_incidents'])
    if incidents.empty:
        print("✗ Cannot load poaching incidents. Exiting.")
        return
    
    rainfall_df = pd.read_csv(DATA_CONFIG['rainfall'], parse_dates=['week_start'])
    moon_df = pd.read_csv(DATA_CONFIG['moon_phases'], parse_dates=['date'])
    
    print(f"✓ Park boundary loaded")
    print(f"✓ Roads: {len(roads)} features")
    print(f"✓ Villages: {len(villages)} features")
    print(f"✓ Water: {len(water)} features")
    print(f"✓ Poaching incidents: {len(incidents)} records ({incidents['date'].min()} to {incidents['date'].max()})")
    print(f"✓ Rainfall: {len(rainfall_df)} weeks")
    print(f"✓ Moon phases: {len(moon_df)} dates")
    
    # Data summary
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)
    print(f"Park bounds: {park_geom.bounds}")
    print(f"Incident date range: {incidents['date'].min()} to {incidents['date'].max()}")
    print(f"Poaching density: {len(incidents) / (incidents['date'].max() - incidents['date'].min()).days:.2f} incidents/day")
    
    print("\n✓ Data validation complete!")
    print("\nNext steps:")
    print("1. Verify summary matches your expectations")
    print("2. Run Colab notebook with these same paths, OR")
    print("3. Implement training script locally using these loaders")
    print("\nIf all looks good, proceed with training!")

if __name__ == '__main__':
    main()
