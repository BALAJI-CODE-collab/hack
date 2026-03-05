import sys
sys.path.insert(0, '/c/Project')

from preprocessing import DataPreprocessor

preprocessor = DataPreprocessor()
print("Before load_all():")
print(f"  park_boundary: {preprocessor.park_boundary}")

preprocessor.load_all()
print("\nAfter load_all():")
print(f"  park_boundary type: {type(preprocessor.park_boundary)}")
print(f"  park_boundary: {preprocessor.park_boundary}")

if preprocessor.park_boundary:
    print(f"  park geom type: {preprocessor.park_boundary.geom_type}")
else:
    print("  ERROR: park_boundary is None!")
