import sys
sys.path.insert(0, 'c:/Project')
from preprocessing import DataPreprocessor

preprocessor = DataPreprocessor()
park = preprocessor.load_all()[0]
print("Park geometry type:", park.geom_type)
if park.geom_type == 'MultiPolygon':
    print(f"Number of regions: {len(list(park.geoms))}")
    for i, geom in enumerate(park.geoms):
        bounds = geom.bounds
        print(f"  Region {i}: Lon {bounds[0]:.1f}-{bounds[2]:.1f}, Lat {bounds[1]:.1f}-{bounds[3]:.1f}")
else:
    print(f"Is Polygon: {park.geom_type}")

# Also check incidents
incidents = preprocessor.poaching_incidents
print(f"\nTotal incidents: {len(incidents)}")
if 'latitude' in incidents.columns:
    print(f"Incident lat range: {incidents['latitude'].min():.1f} to {incidents['latitude'].max():.1f}")
    print(f"Incident lon range: {incidents['longitude'].min():.1f} to {incidents['longitude'].max():.1f}")
