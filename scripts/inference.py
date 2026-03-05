import argparse
from pathlib import Path
import numpy as np
import tensorflow as tf
from PIL import Image


class AnimalClassifier:
    """Inference wrapper for the trained animal classification model."""
    
    def __init__(self, model_path, img_size=(224, 224)):
        """Load the trained model."""
        self.model = tf.keras.models.load_model(model_path)
        self.img_size = img_size
        self.classes = ['elephant', 'tiger', 'lion', 'zebra', 'ox']
    
    def preprocess_image(self, image_path):
        """Load and preprocess a single image."""
        try:
            # Load image
            img = Image.open(image_path).convert('RGB')
            # Resize to model input size
            img = img.resize(self.img_size, Image.Resampling.LANCZOS)
            # Convert to array and normalize (0-1)
            img_array = np.array(img) / 255.0
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            raise ValueError(f"Error processing image {image_path}: {str(e)}")
    
    def predict(self, image_path):
        """
        Predict the class and confidence for a single image.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: {
                'image_path': str,
                'predicted_class': str,
                'confidence': float (0-100),
                'probabilities': dict of all classes and their probabilities
            }
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Preprocess
        img_array = self.preprocess_image(image_path)
        
        # Predict
        predictions = self.model.predict(img_array, verbose=0)
        pred_class_idx = np.argmax(predictions[0])
        pred_class = self.classes[pred_class_idx]
        confidence = float(predictions[0][pred_class_idx]) * 100
        
        # Get all probabilities
        all_probs = {
            self.classes[i]: float(predictions[0][i]) * 100
            for i in range(len(self.classes))
        }
        
        return {
            'image_path': str(image_path),
            'predicted_class': pred_class,
            'confidence': round(confidence, 2),
            'probabilities': {k: round(v, 2) for k, v in sorted(all_probs.items(), key=lambda x: x[1], reverse=True)}
        }
    
    def predict_batch(self, image_paths):
        """Predict on multiple images."""
        results = []
        for img_path in image_paths:
            try:
                result = self.predict(img_path)
                results.append(result)
            except Exception as e:
                results.append({'image_path': str(img_path), 'error': str(e)})
        return results


def main():
    parser = argparse.ArgumentParser(description='Classify animal images using trained model')
    parser.add_argument('--model', default='outputs/trained_model.h5', help='Path to trained model')
    parser.add_argument('--image', help='Single image path to classify')
    parser.add_argument('--images', nargs='+', help='Multiple image paths to classify')
    parser.add_argument('--dir', help='Directory of images to classify all in it')
    args = parser.parse_args()
    
    # Load model
    classifier = AnimalClassifier(args.model)
    
    # Single image
    if args.image:
        result = classifier.predict(args.image)
        print(f"\n{'='*60}")
        print(f"Image: {result['image_path']}")
        print(f"Predicted Class: {result['predicted_class'].upper()}")
        print(f"Confidence: {result['confidence']}%")
        print(f"All Probabilities:")
        for cls, prob in result['probabilities'].items():
            bar = '█' * int(prob / 5) + '░' * (20 - int(prob / 5))
            print(f"  {cls:10} {bar} {prob:.2f}%")
        print(f"{'='*60}\n")
    
    # Multiple images
    elif args.images:
        results = classifier.predict_batch(args.images)
        for result in results:
            if 'error' in result:
                print(f"❌ {result['image_path']}: {result['error']}")
            else:
                print(f"✓ {result['image_path']}")
                print(f"   Class: {result['predicted_class'].upper() } ({result['confidence']}%)")
    
    # Directory of images
    elif args.dir:
        dir_path = Path(args.dir)
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        images = [str(p) for p in dir_path.rglob('*') if p.suffix.lower() in image_exts]
        if not images:
            print(f"No images found in {args.dir}")
            return
        results = classifier.predict_batch(images)
        correct = sum(1 for r in results if 'predicted_class' in r)
        print(f"\nProcessed {correct}/{len(results)} images from {args.dir}")
        for result in results[:10]:  # Show first 10
            if 'error' not in result:
                print(f"  {Path(result['image_path']).name}: {result['predicted_class'].upper()} ({result['confidence']}%)")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
