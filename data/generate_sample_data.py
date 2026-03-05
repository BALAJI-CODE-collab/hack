"""Generate sample datasets for poaching prediction project."""
import json
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString, mapping
from datetime import datetime, timedelta
import os


def generate_park_boundary(output_path):
    """Create multiple forest regions GeoJSON."""
    # Multiple forest regions spanning the globe
    regions = [
        {
            "name": "Serengeti National Park",
            "coords": [(33.0, -3.0), (36.0, -3.0), (36.0, 0.0), (33.0, 0.0), (33.0, -3.0)],
            "region": "Africa"
        },
        {
            "name": "Amazon Rainforest",
            "coords": [(-75.0, -5.0), (-70.0, -5.0), (-70.0, 0.0), (-75.0, 0.0), (-75.0, -5.0)],
            "region": "South America"
        },
        {
            "name": "Congo Basin",
            "coords": [(15.0, -5.0), (20.0, -5.0), (20.0, 0.0), (15.0, 0.0), (15.0, -5.0)],
            "region": "Africa"
        },
        {
            "name": "Southeast Asia Mangroves",
            "coords": [(105.0, 5.0), (110.0, 5.0), (110.0, 10.0), (105.0, 10.0), (105.0, 5.0)],
            "region": "Asia"
        }
    ]
    
    # Create a union of all regions for preprocessing
    parks = [Polygon(r["coords"]) for r in regions]
    
    features = []
    for region, park in zip(regions, parks):
        features.append({
            "type": "Feature",
            "properties": {"name": region["name"], "region": region["region"]},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x, y] for x, y in park.exterior.coords]]
            }
        })
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(feature_collection, f)
    print(f"[OK] Forest regions saved to {output_path} (4 regions)")
    
    # Return the union of all parks
    from shapely.ops import unary_union
    return unary_union(parks)


def generate_roads(output_path, park_geom, num_roads=5):
    """Create sample road network."""
    roads = []
    
    # Handle both single Polygon and MultiPolygon
    regions = park_geom.geoms if park_geom.geom_type == 'MultiPolygon' else [park_geom]
    roads_per_region = max(1, num_roads // len(regions))
    
    for region in regions:
        minx, miny, maxx, maxy = region.bounds
        for i in range(roads_per_region):
            x1 = np.random.uniform(minx, maxx)
            y1 = np.random.uniform(miny, maxy)
            x2 = np.random.uniform(minx, maxx)
            y2 = np.random.uniform(miny, maxy)
            
            roads.append({
                "type": "Feature",
                "properties": {"road_id": i, "name": f"Road_{i}"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [(x1, y1), (x2, y2)]
                }
            })
    
    fc = {"type": "FeatureCollection", "features": roads}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(fc, f)
    print(f"[OK] Roads saved to {output_path}")


def generate_villages(output_path, park_geom, num_villages=8):
    """Create sample village locations."""
    villages = []
    
    # Handle both single Polygon and MultiPolygon
    regions = park_geom.geoms if park_geom.geom_type == 'MultiPolygon' else [park_geom]
    villages_per_region = max(1, num_villages // len(regions))
    
    village_id = 0
    for region in regions:
        minx, miny, maxx, maxy = region.bounds
        for i in range(villages_per_region):
            x = np.random.uniform(minx, maxx)
            y = np.random.uniform(miny, maxy)
            
            villages.append({
                "type": "Feature",
                "properties": {"village_id": village_id, "name": f"Village_{village_id}", "population": np.random.randint(100, 5000)},
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
                }
            })
            village_id += 1
    
    fc = {"type": "FeatureCollection", "features": villages}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(fc, f)
    print(f"[OK] Villages saved to {output_path}")


def generate_water(output_path, park_geom, num_waterbodies=4):
    """Create sample water bodies."""
    waters = []
    
    # Handle both single Polygon and MultiPolygon
    regions = park_geom.geoms if park_geom.geom_type == 'MultiPolygon' else [park_geom]
    waters_per_region = max(1, num_waterbodies // len(regions))
    
    for region in regions:
        minx, miny, maxx, maxy = region.bounds
        for i in range(waters_per_region):
            cx = np.random.uniform(minx + 0.05, maxx - 0.05)
            cy = np.random.uniform(miny + 0.05, maxy - 0.05)
            radius = np.random.uniform(0.01, 0.05)
            
            water_poly = box(cx - radius, cy - radius, cx + radius, cy + radius)
            waters.append({
                "type": "Feature",
                "properties": {"water_id": i, "name": f"Water_{i}", "type": "lake"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[x, y] for x, y in water_poly.exterior.coords]]
                }
            })
    
    fc = {"type": "FeatureCollection", "features": waters}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(fc, f)
    print(f"[OK] Water bodies saved to {output_path}")


def generate_poaching_incidents(output_path, park_geom, num_incidents=150, date_range=365):
    """Create sample poaching incident data across all forest regions."""
    # Define regions explicitly to ensure incidents span globally
    regions = [
        {'name': 'Serengeti', 'bounds': (33.0, -3.0, 36.0, 0.0)},
        {'name': 'Amazon', 'bounds': (-75.0, -5.0, -70.0, 0.0)},
        {'name': 'Congo', 'bounds': (15.0, -5.0, 20.0, 0.0)},
        {'name': 'SE_Asia', 'bounds': (105.0, 5.0, 110.0, 10.0)}
    ]
    
    incidents = []
    base_date = datetime(2020, 1, 1)
    incidents_per_region = num_incidents // len(regions)
    
    for region_idx, region in enumerate(regions):
        minx, miny, maxx, maxy = region['bounds']
        
        for i in range(incidents_per_region):
            # Random date within range
            days_offset = np.random.randint(0, date_range)
            incident_date = base_date + timedelta(days=days_offset)
            
            # Random location within region
            x = np.random.uniform(minx, maxx)
            y = np.random.uniform(miny, maxy)
            
            incidents.append({
                'date': incident_date.strftime('%Y-%m-%d'),
                'lon': x,
                'lat': y,
                'type': np.random.choice(['poaching', 'attempted_poaching'], p=[0.7, 0.3]),
                'region': region['name']
            })
    
    df = pd.DataFrame(incidents)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Poaching incidents saved to {output_path} ({len(df)} incidents)")


def generate_rainfall(output_path, date_range=365):
    """Create sample weekly rainfall data."""
    base_date = datetime(2020, 1, 1)
    
    rainfall = []
    for week in range(date_range // 7):
        week_start = base_date + timedelta(weeks=week)
        # Rainfall varies seasonally
        seasonal_factor = np.sin(2 * np.pi * week / 52)
        rainfall_mm = max(0, np.random.normal(50 + 30 * seasonal_factor, 15))
        
        rainfall.append({
            'week_start': week_start.strftime('%Y-%m-%d'),
            'rainfall_mm': rainfall_mm
        })
    
    df = pd.DataFrame(rainfall)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Rainfall data saved to {output_path}")


def generate_moon_phases(output_path, date_range=365):
    """Create sample moon phase data."""
    base_date = datetime(2020, 1, 1)
    phases = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous', 
              'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
    
    moon_data = []
    for day in range(date_range):
        date = base_date + timedelta(days=day)
        # Moon cycles roughly every 29.5 days
        phase_idx = int((day % 29.5) / (29.5 / 8))
        lunar_illumination = (1 - np.cos(2 * np.pi * (day % 29.5) / 29.5)) / 2
        
        moon_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'phase': phases[phase_idx],
            'illumination': lunar_illumination
        })
    
    df = pd.DataFrame(moon_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Moon phase data saved to {output_path}")


def generate_ndvi(output_path, park_geom, grid_size=10):
    """Create sample NDVI raster (as CSV for simplicity)."""
    minx, miny, maxx, maxy = park_geom.bounds
    
    ndvi_data = []
    for i in np.linspace(minx, maxx, grid_size):
        for j in np.linspace(miny, maxy, grid_size):
            # NDVI typically higher near water, lower in bare ground
            dist_to_center = np.sqrt((i - 34.5)**2 + (j + 1.5)**2)
            ndvi = 0.6 - 0.2 * dist_to_center + np.random.normal(0, 0.05)
            ndvi = np.clip(ndvi, -1, 1)
            
            ndvi_data.append({
                'lon': i,
                'lat': j,
                'ndvi': ndvi
            })
    
    df = pd.DataFrame(ndvi_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] NDVI data saved to {output_path}")


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    
    # Generate park boundary first
    park = generate_park_boundary('data/park_boundary.geojson')
    
    # Generate all other datasets
    generate_roads('data/roads.geojson', park, num_roads=5)
    generate_villages('data/villages.geojson', park, num_villages=8)
    generate_water('data/water.geojson', park, num_waterbodies=4)
    generate_poaching_incidents('data/poaching_incidents.csv', park, num_incidents=150, date_range=365)
    generate_rainfall('data/rainfall.csv', date_range=365)
    generate_moon_phases('data/moon_phases.csv', date_range=365)
    generate_ndvi('data/ndvi.csv', park, grid_size=10)
    
    print("\n[OK] All sample datasets generated successfully!")