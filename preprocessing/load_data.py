import pandas as pd
import json
from shapely.geometry import shape, Point

def load_poaching(path):
    df = pd.read_csv(path, parse_dates=['date'])
    # create shapely Points
    df['geometry'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
    return df

def load_geojson_geoms(path):
    # returns list of (geom, properties)
    with open(path, 'r') as f:
        coll = json.load(f)
    res = []
    for feat in coll.get('features', []):
        geom = shape(feat['geometry'])
        props = feat.get('properties', {})
        res.append((geom, props))
    return res

