#!/usr/bin/env python3
import json

with open('outputs/risk_heatmap.geojson') as f:
    d = json.load(f)

print(f'Total cells in risk_heatmap.geojson: {len(d["features"])}')

regions = {}
for feature in d['features']:
    region = feature['properties']['grid_id'].split('_')[0]
    regions[region] = regions.get(region, 0) + 1

print('Cells per region:')
for region in sorted(regions.keys()):
    print(f'  Region {region}: {regions[region]} cells')
