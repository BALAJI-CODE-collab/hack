import argparse
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix


def build_model(num_classes, input_shape=(224, 224, 3), dropout_rate=0.5):
    base = tf.keras.applications.MobileNetV2(
        input_shape=input_shape, include_top=False, weights="imagenet", pooling="avg"
    )
    base.trainable = False
    x = base.output
    x = tf.keras.layers.Dropout(dropout_rate)(x)
    out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs=base.input, outputs=out)
    return model


def save_confusion_matrix(cm, labels, out_path):
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="black")
    fig.colorbar(im)
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def run(args):
    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img_size = (224, 224)
    target_classes = ['elephant', 'tiger', 'lion', 'zebra', 'ox']

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=0.2,
        horizontal_flip=True,
        rotation_range=15,
        brightness_range=(0.8, 1.2),
        zoom_range=0.15,
    )

    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255.0)

    train_generator = train_datagen.flow_from_directory(
        directory=str(data_dir),
        target_size=img_size,
        batch_size=args.batch_size,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42,
        classes=target_classes,
    )

    val_generator = train_datagen.flow_from_directory(
        directory=str(data_dir),
        target_size=img_size,
        batch_size=args.batch_size,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42,
        classes=target_classes,
    )

    num_classes = len(train_generator.class_indices)
    labels = [k for k, v in sorted(train_generator.class_indices.items(), key=lambda x: x[1])]

    model = build_model(num_classes=num_classes)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(str(out_dir / "best_model.h5"), save_best_only=True, monitor="val_loss"),
    ]

    model.fit(
        train_generator,
        epochs=args.epochs,
        validation_data=val_generator,
        callbacks=callbacks,
    )

    # evaluation on validation (treated as test here)
    val_steps = int(np.ceil(val_generator.samples / args.batch_size))
    y_true = []
    y_pred = []
    y_prob = []
    filenames = []

    val_generator.reset()
    for i in range(val_steps):
        x_batch, y_batch = next(val_generator)
        probs = model.predict(x_batch)
        preds = np.argmax(probs, axis=1)
        truths = np.argmax(y_batch, axis=1)
        y_true.extend(truths.tolist())
        y_pred.extend(preds.tolist())
        y_prob.extend(probs.max(axis=1).tolist())
    # map indices to labels
    y_true_labels = [labels[i] for i in y_true]
    y_pred_labels = [labels[i] for i in y_pred]

    report = classification_report(y_true_labels, y_pred_labels, output_dict=True)
    cm = confusion_matrix(y_true_labels, y_pred_labels, labels=labels)

    # save outputs
    with open(out_dir / "class_performance.json", "w") as f:
        json.dump(report, f, indent=2)

    save_confusion_matrix(cm, labels, out_dir / "confusion_matrix.png")

    # sample predictions CSV
    df = pd.DataFrame({"true_label": y_true_labels, "pred_label": y_pred_labels, "confidence": y_prob})
    df.to_csv(out_dir / "sample_predictions.csv", index=False)

    # save final model
    model.save(out_dir / "trained_model.h5")

    print("Training complete. Outputs saved to:", out_dir)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", required=True, help="Path to dataset directory (subfolders per class)")
    p.add_argument("--output-dir", default="outputs", help="Where to save models and metrics")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--learning-rate", type=float, default=1e-3)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args)
