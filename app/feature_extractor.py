import os
import numpy as np
import pandas as pd
import rasterio


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MAIN_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "Dataset of Sentinel-1 SAR and Sentinel-2 NDVI Imagery",
    "Main Folder"
)

DATA_FILE = os.path.join(
    MAIN_FOLDER,
    "DATA.xlsx"
)

NDVI_FOLDER = os.path.join(
    MAIN_FOLDER,
    "NDVI"
)

RGB_FOLDER = os.path.join(
    MAIN_FOLDER,
    "RGB"
)

VV_FOLDER = os.path.join(
    MAIN_FOLDER,
    "SAR",
    "VV"
)

VH_FOLDER = os.path.join(
    MAIN_FOLDER,
    "SAR",
    "VH"
)


# ============================================================
# LOAD METADATA
# ============================================================

metadata = pd.read_excel(DATA_FILE)


# ============================================================
# CALCULATE IMAGE STATISTICS
# ============================================================

def calculate_statistics(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Satellite file not found:\n{file_path}"
        )

    with rasterio.open(file_path) as dataset:

        image = dataset.read().astype(np.float64)

    mean_value = float(np.nanmean(image))
    std_value = float(np.nanstd(image))

    return mean_value, std_value


# ============================================================
# EXTRACT COMPLETE 24 FEATURES
# ============================================================

def extract_all_features(record_id):

    record_id = int(record_id)

    # --------------------------------------------------------
    # CHECK RECORD
    # --------------------------------------------------------

    if record_id < 0 or record_id >= len(metadata):

        raise ValueError(
            f"Record ID must be between 0 and {len(metadata) - 1}"
        )

    row = metadata.iloc[record_id]


    # --------------------------------------------------------
    # METADATA FEATURES
    # --------------------------------------------------------

    initial_date = pd.to_datetime(row["Initial dates"])
    end_date = pd.to_datetime(row["End dates"])

    duration_days = (
        end_date - initial_date
    ).days

    features = {

        "Latitud":
            float(row["Latitud"]),

        "Longitudes":
            float(row["Longitudes"]),

        "Cloudiness Mean":
            float(row["Cloudiness Mean"]),

        "Water percentage Mean":
            float(row["Water percentage Mean"]),

        "Vegetation percentage Mean":
            float(row["Vegetation percentage Mean"]),

        "Year":
            float(initial_date.year),

        "Month":
            float(initial_date.month),

        "Duration_Days":
            float(duration_days)
    }


    # --------------------------------------------------------
    # PERIOD A
    # --------------------------------------------------------

    ndvi_a = os.path.join(
        NDVI_FOLDER,
        f"{record_id}A.tif"
    )

    rgb_a = os.path.join(
        RGB_FOLDER,
        f"{record_id}A.tif"
    )

    vv_a = os.path.join(
        VV_FOLDER,
        f"{record_id}A.tif"
    )

    vh_a = os.path.join(
        VH_FOLDER,
        f"{record_id}A.tif"
    )


    features["NDVI_Mean_A"], \
    features["NDVI_Std_A"] = \
        calculate_statistics(ndvi_a)

    features["RGB_Mean_A"], \
    features["RGB_Std_A"] = \
        calculate_statistics(rgb_a)

    features["VV_Mean_A"], \
    features["VV_Std_A"] = \
        calculate_statistics(vv_a)

    features["VH_Mean_A"], \
    features["VH_Std_A"] = \
        calculate_statistics(vh_a)


    # --------------------------------------------------------
    # PERIOD B
    # --------------------------------------------------------

    ndvi_b = os.path.join(
        NDVI_FOLDER,
        f"{record_id}B.tif"
    )

    rgb_b = os.path.join(
        RGB_FOLDER,
        f"{record_id}B.tif"
    )

    vv_b = os.path.join(
        VV_FOLDER,
        f"{record_id}B.tif"
    )

    vh_b = os.path.join(
        VH_FOLDER,
        f"{record_id}B.tif"
    )


    features["NDVI_Mean_B"], \
    features["NDVI_Std_B"] = \
        calculate_statistics(ndvi_b)

    features["RGB_Mean_B"], \
    features["RGB_Std_B"] = \
        calculate_statistics(rgb_b)

    features["VV_Mean_B"], \
    features["VV_Std_B"] = \
        calculate_statistics(vv_b)

    features["VH_Mean_B"], \
    features["VH_Std_B"] = \
        calculate_statistics(vh_b)


    return features