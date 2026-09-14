import os
import sys

import numpy as np
import pandas as pd
import rasterio
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report


# ============================================================
# PROJECT PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BASE_DIR = os.path.dirname(
    CURRENT_DIR
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

FEATURE_DIR = os.path.join(
    DATA_DIR,
    "features"
)

RAW_DIR = os.path.join(
    DATA_DIR,
    "raw"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

IMAGE_MODEL_DIR = os.path.join(
    BASE_DIR,
    "image_model"
)


# ============================================================
# FILE PATHS
# ============================================================

PREDICTION_FILE = os.path.join(
    FEATURE_DIR,
    "drought_predictions.csv"
)

MAIN_FOLDER = os.path.join(
    RAW_DIR,
    "Dataset of Sentinel-1 SAR and Sentinel-2 NDVI Imagery",
    "Main Folder"
)

NDVI_FOLDER = os.path.join(
    MAIN_FOLDER,
    "NDVI"
)


# ============================================================
# OUTPUT FILES
# ============================================================

IMAGE_MODEL_FILE = os.path.join(
    IMAGE_MODEL_DIR,
    "image_drought_model.pkl"
)

IMAGE_SCALER_FILE = os.path.join(
    IMAGE_MODEL_DIR,
    "image_feature_scaler.pkl"
)


# ============================================================
# IMAGE FEATURE EXTRACTION
# ============================================================

def calculate_image_features(
    file_path
):

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Image not found: {file_path}"
        )


    with rasterio.open(
        file_path
    ) as dataset:

        image = dataset.read().astype(
            np.float64
        )


    image = np.nan_to_num(
        image,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )


    return [

        float(np.mean(image)),

        float(np.std(image)),

        float(np.min(image)),

        float(np.max(image)),

        float(np.median(image))

    ]


# ============================================================
# LOAD EXISTING PREDICTIONS
# ============================================================

print()
print("=" * 60)
print(" IMAGE DROUGHT MODEL TRAINING")
print("=" * 60)
print()


if not os.path.exists(
    PREDICTION_FILE
):

    print(
        "ERROR: drought_predictions.csv not found."
    )

    sys.exit(1)


predictions_df = pd.read_csv(
    PREDICTION_FILE
)


print(
    "Prediction dataset loaded."
)

print(
    "Records:",
    len(predictions_df)
)


# ============================================================
# BUILD IMAGE DATASET
# ============================================================

X = []

y = []

record_ids = []


print()
print(
    "Extracting NDVI image features..."
)
print("-" * 60)


for _, row in predictions_df.iterrows():

    record_id = int(
        row["record_id"]
    )


    image_path = os.path.join(
        NDVI_FOLDER,
        f"{record_id}A.tif"
    )


    try:

        features = calculate_image_features(
            image_path
        )


        X.append(
            features
        )

        y.append(
            str(row["prediction"])
        )

        record_ids.append(
            record_id
        )


        if len(X) % 100 == 0:

            print(
                f"Processed {len(X)}/"
                f"{len(predictions_df)}"
            )


    except Exception as e:

        print(
            f"Skipping record "
            f"{record_id}: {e}"
        )


# ============================================================
# CONVERT TO DATAFRAME
# ============================================================

X = np.array(
    X,
    dtype=np.float64
)

y = np.array(
    y
)


print()
print(
    "Image feature extraction completed."
)

print(
    "Samples:",
    len(X)
)

print(
    "Features per image:",
    X.shape[1]
)


# ============================================================
# CHECK DATA
# ============================================================

if len(X) < 10:

    print(
        "ERROR: Not enough image samples."
    )

    sys.exit(1)


print()
print(
    "Class distribution:"
)

print(
    pd.Series(y).value_counts()
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y

)


# ============================================================
# FEATURE SCALING
# ============================================================

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(
    X_train
)

X_test_scaled = scaler.transform(
    X_test
)


# ============================================================
# TRAIN RANDOM FOREST
# ============================================================

print()
print(
    "Training image drought model..."
)


image_model = RandomForestClassifier(

    n_estimators=300,

    random_state=42,

    class_weight="balanced",

    n_jobs=-1

)


image_model.fit(
    X_train_scaled,
    y_train
)


print(
    "✓ Image model trained successfully."
)


# ============================================================
# EVALUATION
# ============================================================

y_pred = image_model.predict(
    X_test_scaled
)


accuracy = accuracy_score(
    y_test,
    y_pred
)


print()
print("=" * 60)
print(" MODEL EVALUATION")
print("=" * 60)

print()

print(
    f"Test Accuracy: {accuracy:.4f}"
)

print()

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

os.makedirs(
    IMAGE_MODEL_DIR,
    exist_ok=True
)


joblib.dump(
    image_model,
    IMAGE_MODEL_FILE
)


joblib.dump(
    scaler,
    IMAGE_SCALER_FILE
)


# ============================================================
# SAVE FEATURE INFORMATION
# ============================================================

feature_names = [

    "image_mean",

    "image_std",

    "image_min",

    "image_max",

    "image_median"

]


feature_info_file = os.path.join(

    IMAGE_MODEL_DIR,

    "image_feature_names.txt"

)


with open(
    feature_info_file,
    "w"
) as file:

    for feature in feature_names:

        file.write(
            feature + "\n"
        )


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)
print(" IMAGE MODEL TRAINING COMPLETED")
print("=" * 60)

print()

print(
    "Model saved:"
)

print(
    IMAGE_MODEL_FILE
)

print()

print(
    "Scaler saved:"
)

print(
    IMAGE_SCALER_FILE
)

print()

print(
    "Feature information saved:"
)

print(
    feature_info_file
)

print()

print(
    "Ready for the uploaded-image prediction stage."
)

print(
    "=" * 60
)