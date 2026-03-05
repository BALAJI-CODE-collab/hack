import tensorflow as tf
import numpy as np
from PIL import Image # For image loading and resizing
import os # For path manipulation

# Define constants (must match training setup)
IMG_HEIGHT = 224
IMG_WIDTH = 224
CLASS_NAMES = ['elephant', 'lion', 'ox', 'tiger', 'zebra'] # Your class names

# 1. Load the trained model
try:
    model = tf.keras.models.load_model('trained_model.h5')
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# 2. Preprocessing function (must match the one used during training)
def preprocess_image(image_path):
    img = Image.open(image_path).resize((IMG_WIDTH, IMG_HEIGHT))
    img_array = np.array(img).astype(np.float32) # Convert to numpy array and float32
    # Ensure 3 channels for grayscale images if necessary (MobileNetV2 expects 3 channels)
    if img_array.ndim == 2:
        img_array = np.stack([img_array, img_array, img_array], axis=-1)
    elif img_array.shape[-1] == 4: # Handle RGBA images
        img_array = img_array[:, :, :3]
    img_array = img_array / 255.0 # Normalize to [0, 1]
    return np.expand_dims(img_array, axis=0) # Add batch dimension

# 3. Example: Make a prediction on a new image
# Replace 'path/to/your/new_image.jpg' with the actual path to an image you want to classify
new_image_path = 'path/to/your/new_image.jpg' # Example path

# Create a dummy image for demonstration if the path doesn't exist
if not os.path.exists(new_image_path):
    print(f"Creating a dummy image for demonstration at {new_image_path}")
    dummy_image = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), color = 'red')
    os.makedirs(os.path.dirname(new_image_path) or '.', exist_ok=True)
    dummy_image.save(new_image_path)

preprocessed_img = preprocess_image(new_image_path)

print(f"\nMaking prediction for: {new_image_path}")
predictions = model.predict(preprocessed_img)
predicted_class_idx = np.argmax(predictions[0])
predicted_class_name = CLASS_NAMES[predicted_class_idx]
confidence = predictions[0][predicted_class_idx]

print(f"Predicted class: {predicted_class_name} (Confidence: {confidence:.2f})")
print(f"All probabilities: {predictions[0]}")