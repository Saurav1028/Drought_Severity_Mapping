import os
import sys

import numpy as np
import pandas as pd
import joblib


# ============================================================
# PROJECT PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

BASE_DIR = os.path.dirname(
    CURRENT_DIR
)


# ============================================================
# MODEL PATHS
# ============================================================

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "final_drought_model.pkl"
)

SCALER_FILE = os.path.join(
    MODEL_DIR,
    "final_feature_scaler.pkl"
)


# ============================================================
# OUTPUT PATH
# ============================================================

FEATURE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "features"
)

OUTPUT_FILE = os.path.join(
    FEATURE_DIR,
    "drought_predictions.csv"
)


# ============================================================
# IMPORT FEATURE EXTRACTOR
# ============================================================

try:

    from feature_extractor import (
        extract_all_features
    )

except ImportError as e:

    print(
        "\nERROR: Could not import feature_extractor.py"
    )

    print(
        "Make sure generate_predictions.py "
        "is in the same folder as feature_extractor.py."
    )

    print(
        "\nDetails:",
        e
    )

    sys.exit(1)


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

print("\n==============================================")
print(" DROUGHT PREDICTION GENERATION")
print("==============================================\n")


if not os.path.exists(MODEL_FILE):

    print(
        "ERROR: Model file not found:"
    )

    print(
        MODEL_FILE
    )

    sys.exit(1)


if not os.path.exists(SCALER_FILE):

    print(
        "ERROR: Scaler file not found:"
    )

    print(
        SCALER_FILE
    )

    sys.exit(1)


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "Loading trained model..."
)

model = joblib.load(
    MODEL_FILE
)

print(
    "✓ Model loaded successfully."
)


# ============================================================
# LOAD SCALER
# ============================================================

print(
    "Loading feature scaler..."
)

scaler = joblib.load(
    SCALER_FILE
)

print(
    "✓ Scaler loaded successfully."
)


# ============================================================
# FIND NUMBER OF RECORDS
# ============================================================

# feature_extractor.py already loads DATA.xlsx
# as the global variable "metadata".

try:

    from feature_extractor import metadata

except ImportError:

    print(
        "ERROR: Could not access metadata."
    )

    sys.exit(1)


total_records = len(
    metadata
)


print(
    f"\nTotal records found: {total_records}"
)


# ============================================================
# EXTRACT FEATURES
# ============================================================

all_feature_rows = []

successful_records = []

failed_records = []


print(
    "\nExtracting 24 features from records..."
)

print(
    "----------------------------------------------"
)


for record_id in range(
    total_records
):

    try:

        features = extract_all_features(
            record_id
        )

        all_feature_rows.append(
            features
        )

        successful_records.append(
            record_id
        )


        if (
            (record_id + 1) % 50 == 0
            or
            record_id == total_records - 1
        ):

            print(
                f"Processed "
                f"{record_id + 1}/"
                f"{total_records}"
            )


    except Exception as e:

        failed_records.append({

            "record_id":
                record_id,

            "error":
                str(e)

        })


        print(
            f"⚠ Record {record_id} failed: {e}"
        )


# ============================================================
# CHECK EXTRACTION
# ============================================================

if len(all_feature_rows) == 0:

    print(
        "\nERROR: No features were extracted."
    )

    sys.exit(1)


features_df = pd.DataFrame(
    all_feature_rows
)


print(
    "\nFeature extraction completed."
)

print(
    "Successful records:",
    len(successful_records)
)

print(
    "Failed records:",
    len(failed_records)
)

print(
    "Feature shape:",
    features_df.shape
)


# ============================================================
# DISPLAY FEATURE NAMES
# ============================================================

print(
    "\nFeatures extracted:"
)

for index, column in enumerate(
    features_df.columns,
    start=1
):

    print(
        f"{index:02d}. {column}"
    )


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

X = features_df.copy()


# ============================================================
# HANDLE NUMERIC VALUES
# ============================================================

X = X.apply(
    pd.to_numeric,
    errors="coerce"
)


# ============================================================
# CHECK MISSING VALUES
# ============================================================

if X.isnull().any().any():

    print(
        "\nWARNING: Missing values detected."
    )

    print(
        X.isnull().sum()
    )


    # Use column median only for any
    # unexpected missing values.

    X = X.fillna(
        X.median()
    )


# ============================================================
# APPLY FEATURE SCALER
# ============================================================

print(
    "\nScaling features..."
)


try:

    X_scaled = scaler.transform(
        X
    )

except Exception as e:

    print(
        "\nERROR while scaling features:"
    )

    print(
        e
    )

    print(
        "\nNumber of extracted features:",
        X.shape[1]
    )

    print(
        "Feature names:",
        X.columns.tolist()
    )

    sys.exit(1)


print(
    "✓ Features scaled successfully."
)


# ============================================================
# MODEL PREDICTION
# ============================================================

print(
    "\nGenerating drought predictions..."
)


try:

    predictions = model.predict(
        X_scaled
    )

except Exception as e:

    print(
        "\nERROR while generating predictions:"
    )

    print(
        e
    )

    sys.exit(1)


print(
    "✓ Predictions generated successfully."
)


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

result_df = features_df.copy()


# ============================================================
# ADD RECORD ID
# ============================================================

result_df.insert(
    0,
    "record_id",
    successful_records
)


# ============================================================
# ADD PREDICTION
# ============================================================

result_df["prediction"] = [
    str(prediction)
    for prediction in predictions
]


# ============================================================
# ADD FRIENDLY COLUMN NAMES FOR WEBSITE
# ============================================================

rename_columns = {

    "Latitud":
        "latitude",

    "Longitudes":
        "longitude",

    "Cloudiness Mean":
        "cloudiness",

    "Water percentage Mean":
        "water_percentage",

    "Vegetation percentage Mean":
        "vegetation_percentage",

    "Year":
        "year",

    "Month":
        "month",

    "Duration_Days":
        "duration_days",

    "NDVI_Mean_A":
        "ndvi_A",

    "NDVI_Std_A":
        "ndvi_std_A",

    "RGB_Mean_A":
        "rgb_A",

    "RGB_Std_A":
        "rgb_std_A",

    "VV_Mean_A":
        "vv_A",

    "VV_Std_A":
        "vv_std_A",

    "VH_Mean_A":
        "vh_A",

    "VH_Std_A":
        "vh_std_A",

    "NDVI_Mean_B":
        "ndvi_B",

    "NDVI_Std_B":
        "ndvi_std_B",

    "RGB_Mean_B":
        "rgb_B",

    "RGB_Std_B":
        "rgb_std_B",

    "VV_Mean_B":
        "vv_B",

    "VV_Std_B":
        "vv_std_B",

    "VH_Mean_B":
        "vh_B",

    "VH_Std_B":
        "vh_std_B"

}


result_df = result_df.rename(
    columns=rename_columns
)


# ============================================================
# ADD NDVI CHANGE
# ============================================================

if (
    "ndvi_A" in result_df.columns
    and
    "ndvi_B" in result_df.columns
):

    result_df["ndvi_change"] = (

        result_df["ndvi_B"]
        -
        result_df["ndvi_A"]

    )


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    FEATURE_DIR,
    exist_ok=True
)


# ============================================================
# SAVE PREDICTIONS
# ============================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n=============================================="
)

print(
    " PREDICTION GENERATION COMPLETED"
)

print(
    "=============================================="
)


print(
    "\nOutput file:"
)

print(
    OUTPUT_FILE
)


print(
    "\nRecords successfully processed:",
    len(result_df)
)


print(
    "Records failed:",
    len(failed_records)
)


print(
    "\nPrediction distribution:"
)

print(
    result_df[
        "prediction"
    ].value_counts()
)


print(
    "\nOutput shape:",
    result_df.shape
)


print(
    "\nFirst 5 predictions:"
)

print(
    result_df[
        [
            "record_id",
            "latitude",
            "longitude",
            "year",
            "month",
            "ndvi_A",
            "ndvi_B",
            "prediction"
        ]
    ].head()
)


# ============================================================
# FAILED RECORD REPORT
# ============================================================

if failed_records:

    failed_file = os.path.join(

        FEATURE_DIR,

        "failed_prediction_records.csv"

    )


    pd.DataFrame(
        failed_records
    ).to_csv(
        failed_file,
        index=False
    )


    print(
        "\nFailed-record report saved to:"
    )

    print(
        failed_file
    )


print(
    "\n=============================================="
)

print(
    " DONE"
)

print(
    "==============================================\n"
)