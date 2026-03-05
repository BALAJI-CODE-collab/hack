# Local Image Classifier (5 animals)

This repository contains a local training script to train an image classifier on five animal classes: `elephant`, `tiger`, `lion`, `zebra`, `ox`.

Run locally (example):

```bash
python -m pip install -r requirements.txt
python scripts/train_image_classifier.py --data-dir "C:\\Users\\<you>\\Downloads\\archive\\animals\\animals" --output-dir outputs --epochs 20 --batch-size 16
```

Replace the `--data-dir` path with your local images folder (it should contain subfolders per class).

Outputs saved to `outputs/` by default:

- `trained_model.h5`
- `best_model.h5`
- `class_performance.json`
- `confusion_matrix.png`
- `sample_predictions.csv`
# Poaching Activity Prediction using Historical Spatio-Temporal Data

Project to predict weekly poaching risk per 1km grid cell inside a national park and produce GIS heatmaps and patrol priority zones.

Structure
- `data/` - sample data generator and raw inputs
- `preprocessing/` - data loading and spatial preprocessing
- `feature_engineering/` - static & dynamic feature computation
- `models/` - training, tuning, and model persistence
- `evaluation/` - metrics and reports
- `visualization/` - GIS heatmap and patrol route generation
- `main.py` - run end-to-end pipeline

Quick start
1. Create a Python environment and install deps:
```bash
pip install -r requirements.txt
```
2. Generate sample data (if you don't have real data):
```bash
python data/generate_sample_data.py
```
3. Run the pipeline:
```bash
python main.py
```

Notes
- Update `main.py` config paths to point to your real datasets if available.
- The pipeline supports creating synthetic sample data for testing.