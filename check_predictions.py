import json
import pandas as pd
import numpy as np

# Check predictions
with open('outputs/risk_heatmap.geojson') as f:
    geojson = json.load(f)

# Get all grid_ids and their probabilities
grid_probs = {}
for feature in geojson['features']:
    grid_id = feature['properties']['grid_id']
    prob = feature['properties']['risk_probability']
    grid_probs[grid_id] = prob

print(f"Total cells with predictions: {len(grid_probs)}")
print(f"Min probability: {min(grid_probs.values()):.4f}")
print(f"Max probability: {max(grid_probs.values()):.4f}")
print(f"Mean probability: {np.mean(list(grid_probs.values())):.4f}")
print(f"Cells with prob=0: {sum(1 for p in grid_probs.values() if p == 0.0)}")
print(f"Cells with prob>0: {sum(1 for p in grid_probs.values() if p > 0.0)}")

# Show distribution
probs_sorted = sorted(grid_probs.items(), key=lambda x: x[1], reverse=True)
print(f"\nTop 10 cells:")
for grid_id, prob in probs_sorted[:10]:
    print(f"  {grid_id}: {prob:.4f}")
    
print(f"\nBottom 10 cells:")
for grid_id, prob in probs_sorted[-10:]:
    print(f"  {grid_id}: {prob:.4f}")
