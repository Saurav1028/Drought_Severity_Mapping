import os
import io

import numpy as np
import pandas as pd
import joblib
import rasterio

from flask import Flask, render_template, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from location_data_service import (
    read_ndvi_image,
    request_ndvi_for_location,
    request_true_color_for_location
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
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
# PREDICTION DATASET
# ============================================================

PREDICTION_FILE = os.path.join(
    FEATURE_DIR,
    "drought_predictions.csv"
)


# ============================================================
# ORIGINAL MODEL FILES
# ============================================================

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "final_drought_model.pkl"
)

SCALER_FILE = os.path.join(
    MODEL_DIR,
    "final_feature_scaler.pkl"
)


# ============================================================
# IMAGE MODEL FILES
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
# LOAD PREDICTION DATASET
# ============================================================

try:

    prediction_df = pd.read_csv(
        PREDICTION_FILE
    )

    print(
        "Prediction file loaded successfully"
    )

    print(
        "Shape:",
        prediction_df.shape
    )

    print(
        "Columns:",
        prediction_df.columns.tolist()
    )

except Exception as e:

    prediction_df = pd.DataFrame()

    print(
        "Prediction dataset loading error:",
        e
    )


# ============================================================
# LOAD ORIGINAL DROUGHT MODEL
# ============================================================

try:

    model = joblib.load(
        MODEL_FILE
    )

    print(
        "Drought model loaded successfully"
    )

except Exception as e:

    model = None

    print(
        "Model loading error:",
        e
    )


# ============================================================
# LOAD ORIGINAL FEATURE SCALER
# ============================================================

try:

    scaler = joblib.load(
        SCALER_FILE
    )

    print(
        "Feature scaler loaded successfully"
    )

except Exception as e:

    scaler = None

    print(
        "Scaler loading error:",
        e
    )


# ============================================================
# LOAD IMAGE DROUGHT MODEL
# ============================================================

try:

    image_model = joblib.load(
        IMAGE_MODEL_FILE
    )

    print(
        "Image drought model loaded successfully"
    )

except Exception as e:

    image_model = None

    print(
        "Image model loading error:",
        e
    )


# ============================================================
# LOAD IMAGE FEATURE SCALER
# ============================================================

try:

    image_scaler = joblib.load(
        IMAGE_SCALER_FILE
    )

    print(
        "Image feature scaler loaded successfully"
    )

except Exception as e:

    image_scaler = None

    print(
        "Image scaler loading error:",
        e
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({

        "status":
            "running",

        "model_loaded":
            model is not None,

        "scaler_loaded":
            scaler is not None,

        "image_model_loaded":
            image_model is not None,

        "image_scaler_loaded":
            image_scaler is not None,

        "dataset_loaded":
            not prediction_df.empty,

        "records":
            len(prediction_df)

    })


# ============================================================
# LOCATIONS API
# ============================================================

@app.route("/locations")
def locations():

    if prediction_df.empty:

        return jsonify([])


    locations = []


    for _, row in prediction_df.iterrows():

        locations.append({

            "id":
                int(row["record_id"]),

            "latitude":
                float(row["latitude"]),

            "longitude":
                float(row["longitude"]),

            "year":
                int(row["year"]),

            "month":
                int(row["month"]),

            "prediction":
                str(row["prediction"])

        })


    return jsonify(
        locations
    )


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.route("/dashboard-stats")
def dashboard_stats():

    if prediction_df.empty:

        return jsonify({

            "total_locations": 0,

            "low": 0,

            "moderate": 0,

            "severe": 0,

            "extreme": 0,

            "average_ndvi": 0,

            "average_vegetation": 0,

            "average_water": 0

        })


    severity_counts = (
        prediction_df[
            "prediction"
        ]
        .value_counts()
    )


    average_ndvi = 0


    if "ndvi_A" in prediction_df.columns:

        average_ndvi = float(
            prediction_df[
                "ndvi_A"
            ].mean()
        )


    average_vegetation = 0


    if (
        "vegetation_percentage"
        in prediction_df.columns
    ):

        average_vegetation = float(
            prediction_df[
                "vegetation_percentage"
            ].mean()
        )


    average_water = 0


    if (
        "water_percentage"
        in prediction_df.columns
    ):

        average_water = float(
            prediction_df[
                "water_percentage"
            ].mean()
        )


    return jsonify({

        "total_locations":
            int(
                len(prediction_df)
            ),

        "low":
            int(
                severity_counts.get(
                    "Low",
                    0
                )
            ),

        "moderate":
            int(
                severity_counts.get(
                    "Moderate",
                    0
                )
            ),

        "severe":
            int(
                severity_counts.get(
                    "Severe",
                    0
                )
            ),

        "extreme":
            int(
                severity_counts.get(
                    "Extreme",
                    0
                )
            ),

        "average_ndvi":
            average_ndvi,

        "average_vegetation":
            average_vegetation,

        "average_water":
            average_water

    })


# ============================================================
# ANALYTICS API
# ============================================================

@app.route("/analytics")
def analytics():

    if prediction_df.empty:

        return jsonify({})


    severity_counts = (
        prediction_df[
            "prediction"
        ]
        .value_counts()
        .to_dict()
    )


    severity_order = [

        "Low",

        "Moderate",

        "Severe",

        "Extreme"

    ]


    severity_distribution = [

        {

            "severity":
                severity,

            "count":
                int(
                    severity_counts.get(
                        severity,
                        0
                    )
                )

        }

        for severity in severity_order

    ]


    ndvi_by_severity = []


    if (
        "ndvi_A"
        in prediction_df.columns

        and

        "prediction"
        in prediction_df.columns
    ):

        grouped = (
            prediction_df
            .groupby(
                "prediction"
            )[
                "ndvi_A"
            ]
            .mean()
        )


        for severity in severity_order:

            if severity in grouped.index:

                ndvi_by_severity.append({

                    "severity":
                        severity,

                    "value":
                        float(
                            grouped[
                                severity
                            ]
                        )

                })


    vegetation_by_severity = []


    if (
        "vegetation_percentage"
        in prediction_df.columns
    ):

        grouped = (
            prediction_df
            .groupby(
                "prediction"
            )[
                "vegetation_percentage"
            ]
            .mean()
        )


        for severity in severity_order:

            if severity in grouped.index:

                vegetation_by_severity.append({

                    "severity":
                        severity,

                    "value":
                        float(
                            grouped[
                                severity
                            ]
                        )

                })


    year_severity = []


    if (
        "year"
        in prediction_df.columns

        and

        "prediction"
        in prediction_df.columns
    ):

        grouped = (
            prediction_df
            .groupby(
                [
                    "year",
                    "prediction"
                ]
            )
            .size()
            .reset_index(
                name="count"
            )
        )


        for _, row in grouped.iterrows():

            year_severity.append({

                "year":
                    int(
                        row["year"]
                    ),

                "severity":
                    str(
                        row["prediction"]
                    ),

                "count":
                    int(
                        row["count"]
                    )

            })


    return jsonify({

        "severity_distribution":
            severity_distribution,

        "ndvi_by_severity":
            ndvi_by_severity,

        "vegetation_by_severity":
            vegetation_by_severity,

        "year_severity":
            year_severity

    })


# ============================================================
# RECORD INFORMATION
# ============================================================

@app.route(
    "/record/<int:record_id>"
)
def record_information(
    record_id
):

    if prediction_df.empty:

        return jsonify({

            "error":
                "Prediction dataset is empty"

        }), 500


    matching = prediction_df[

        prediction_df[
            "record_id"
        ]
        ==
        record_id

    ]


    if matching.empty:

        return jsonify({

            "error":
                "Record not found"

        }), 404


    row = matching.iloc[0]


    result = {}


    for column in prediction_df.columns:

        value = row[column]


        if pd.isna(value):

            result[column] = None


        elif isinstance(
            value,
            np.integer
        ):

            result[column] = int(
                value
            )


        elif isinstance(
            value,
            np.floating
        ):

            result[column] = float(
                value
            )


        else:

            result[column] = str(
                value
            )


    return jsonify(
        result
    )


# ============================================================
# EXISTING RECORD PREDICTION
# ============================================================

@app.route(
    "/predict-record",
    methods=["POST"]
)
def predict_record():

    try:

        data = request.get_json()

        record_id = int(
            data["record_id"]
        )

    except Exception:

        return jsonify({

            "error":
                "Invalid record ID"

        }), 400


    try:

        if prediction_df.empty:

            return jsonify({

                "error":
                    "Prediction dataset unavailable"

            }), 500


        matching = prediction_df[

            prediction_df[
                "record_id"
            ]
            ==
            record_id

        ]


        if matching.empty:

            return jsonify({

                "error":
                    "Record not found"

            }), 404


        row = matching.iloc[0]


        return jsonify({

            "record_id":
                record_id,

            "latitude":
                float(
                    row["latitude"]
                ),

            "longitude":
                float(
                    row["longitude"]
                ),

            "year":
                int(
                    row["year"]
                ),

            "month":
                int(
                    row["month"]
                ),

            "cloudiness":
                float(
                    row["cloudiness"]
                ),

            "water_percentage":
                float(
                    row["water_percentage"]
                ),

            "vegetation_percentage":
                float(
                    row["vegetation_percentage"]
                ),

            "ndvi_A":
                float(
                    row["ndvi_A"]
                ),

            "ndvi_B":
                float(
                    row["ndvi_B"]
                ),

            "ndvi_change":
                float(
                    row["ndvi_change"]
                ),

            "prediction":
                str(
                    row["prediction"]
                )

        })


    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500


# ============================================================
# SATELLITE IMAGE HELPER
# ============================================================

def find_satellite_file(
    image_type,
    record_id,
    period
):

    main_folder = os.path.join(

        RAW_DIR,

        "Dataset of Sentinel-1 SAR and Sentinel-2 NDVI Imagery",

        "Main Folder"

    )


    folder_map = {

        "ndvi":
            os.path.join(
                main_folder,
                "NDVI"
            ),

        "rgb":
            os.path.join(
                main_folder,
                "RGB"
            ),

        "vv":
            os.path.join(
                main_folder,
                "SAR",
                "VV"
            ),

        "vh":
            os.path.join(
                main_folder,
                "SAR",
                "VH"
            )

    }


    if image_type not in folder_map:

        return None


    folder = folder_map[
        image_type
    ]


    filename = (

        f"{int(record_id)}"

        f"{period}.tif"

    )


    return os.path.join(
        folder,
        filename
    )


# ============================================================
# SATELLITE IMAGE API
# ============================================================

@app.route(
    "/satellite/<image_type>/<int:record_id>/<period>"
)
def satellite_image(
    image_type,
    record_id,
    period
):

    image_type = image_type.lower()

    period = period.upper()


    if period not in [
        "A",
        "B"
    ]:

        return jsonify({

            "error":
                "Period must be A or B"

        }), 400


    file_path = find_satellite_file(

        image_type,

        record_id,

        period

    )


    if file_path is None:

        return jsonify({

            "error":
                "Invalid image type"

        }), 400


    if not os.path.exists(
        file_path
    ):

        return jsonify({

            "error":
                "Satellite image not found"

        }), 404


    try:

        from PIL import Image


        with rasterio.open(
            file_path
        ) as dataset:

            image = dataset.read()


        image = image.astype(
            np.float32
        )


        image = np.nan_to_num(

            image,

            nan=0.0,

            posinf=0.0,

            neginf=0.0

        )


        min_value = float(
            image.min()
        )

        max_value = float(
            image.max()
        )


        if max_value > min_value:

            image = (

                image - min_value

            ) / (

                max_value - min_value

            )

        else:

            image = np.zeros_like(
                image
            )


        image = (

            image * 255

        ).clip(

            0,

            255

        ).astype(
            np.uint8
        )


        if image.shape[0] == 1:

            pil_image = Image.fromarray(

                image[0],

                mode="L"

            )


        elif image.shape[0] >= 3:

            rgb = np.transpose(

                image[:3],

                (1, 2, 0)

            )


            pil_image = Image.fromarray(

                rgb,

                mode="RGB"

            )


        else:

            pil_image = Image.fromarray(

                image[0],

                mode="L"

            )


        buffer = io.BytesIO()


        pil_image.save(

            buffer,

            format="PNG"

        )


        buffer.seek(0)


        return send_file(

            buffer,

            mimetype="image/png",

            as_attachment=False,

            download_name=(

                f"{image_type}_"

                f"{record_id}_"

                f"{period}.png"

            )

        )


    except Exception as e:

        return jsonify({

            "error":
                str(e)

        }), 500

# ============================================================
# SERVE LIVE TRUE-COLOR SATELLITE IMAGE
# ============================================================

@app.route("/live-satellite/true-color/<filename>")
def serve_true_color_image(filename):

    true_color_folder = os.path.join(
        BASE_DIR,
        "data",
        "live_satellite",
        "true_color"
    )

    return send_from_directory(
        true_color_folder,
        filename
    )


# ============================================================
# LIVE LOCATION + IMAGE ANALYSIS
# ============================================================

def extract_uploaded_image_features(image):
    image = image.astype(
        np.float64
    )

    image = np.nan_to_num(
        image,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    features = [
        float(np.mean(image)),
        float(np.std(image)),
        float(np.min(image)),
        float(np.max(image)),
        float(np.median(image))
    ]

    return np.array(
        features,
        dtype=np.float64
    ).reshape(
        1,
        -1
    )


# ============================================================
# LIVE LOCATION ANALYSIS
# ============================================================

@app.route(
    "/analyze-location",
    methods=["POST"]
)
def analyze_location():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No location data received."
            }), 400

        latitude = float(
            data["latitude"]
        )

        longitude = float(
            data["longitude"]
        )

        if latitude < -90 or latitude > 90:
            return jsonify({
                "success": False,
                "error": "Latitude must be between -90 and 90."
            }), 400

        if longitude < -180 or longitude > 180:
            return jsonify({
                "success": False,
                "error": "Longitude must be between -180 and 180."
            }), 400

        start_date = data.get(
            "start_date",
            "2025-08-01"
        )

        end_date = data.get(
            "end_date",
            "2025-08-31"
        )

        if image_model is None:
            return jsonify({
                "success": False,
                "error": "Image drought model is not loaded."
            }), 500

        if image_scaler is None:
            return jsonify({
                "success": False,
                "error": "Image feature scaler is not loaded."
            }), 500

        # ----------------------------------------------------
        # REQUEST LIVE SENTINEL-2 NDVI
        # ----------------------------------------------------

        ndvi_file = request_ndvi_for_location(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )

        # ----------------------------------------------------
        # REQUEST TRUE-COLOR SATELLITE IMAGE
        # ----------------------------------------------------

        true_color_file = request_true_color_for_location(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )

        # ----------------------------------------------------
        # READ NDVI INFORMATION
        # ----------------------------------------------------

        ndvi_result = read_ndvi_image(
            ndvi_file
        )

        statistics = ndvi_result["statistics"]

        metadata = ndvi_result["metadata"]

        # ----------------------------------------------------
        # READ NDVI TIFF
        # ----------------------------------------------------

        with rasterio.open(
            ndvi_file
        ) as dataset:

            image = dataset.read().astype(
                np.float64
            )

        # ----------------------------------------------------
        # CLEAN IMAGE VALUES
        # ----------------------------------------------------

        image = np.nan_to_num(
            image,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        # ----------------------------------------------------
        # EXTRACT SAME 5 FEATURES USED BY IMAGE MODEL
        # ----------------------------------------------------

        image_features = (
            extract_uploaded_image_features(
                image
            )
        )

        # ----------------------------------------------------
        # SCALE FEATURES
        # ----------------------------------------------------

        scaled_features = (
            image_scaler.transform(
                image_features
            )
        )

        # ----------------------------------------------------
        # PREDICT DROUGHT SEVERITY
        # ----------------------------------------------------

        prediction = image_model.predict(
            scaled_features
        )

        predicted_class = str(
            prediction[0]
        )

        # ----------------------------------------------------
        # PREDICTION PROBABILITIES
        # ----------------------------------------------------

        probabilities = {}

        if hasattr(
            image_model,
            "predict_proba"
        ):

            probability_values = (
                image_model.predict_proba(
                    scaled_features
                )[0]
            )

            classes = image_model.classes_

            for class_name, probability in zip(
                classes,
                probability_values
            ):

                probabilities[
                    str(class_name)
                ] = round(
                    float(probability) * 100,
                    2
                )

        confidence = probabilities.get(
            predicted_class,
            None
        )

        # ----------------------------------------------------
        # RETURN LIVE LOCATION RESULT
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "mode":
                "live_satellite",

            "requested_location": {

                "latitude":
                    latitude,

                "longitude":
                    longitude
            },

            "date_range": {

                "start":
                    start_date,

                "end":
                    end_date
            },

            "satellite": {

                "source":
                    "Sentinel-2 L2A",

                "index":
                    "NDVI"
            },

            "prediction":
                predicted_class,

            "predicted_severity":
                predicted_class,

            "confidence":
                confidence,

            "probabilities":
                probabilities,

            "ndvi": {

                "mean":
                    statistics["mean"],

                "standard_deviation":
                    statistics["standard_deviation"],

                "minimum":
                    statistics["minimum"],

                "maximum":
                    statistics["maximum"],

                "median":
                    statistics["median"],

                "valid_pixels":
                    statistics["valid_pixels"]
            },

            "metadata":
                metadata,

            "files": {

                "ndvi": {

                    "filename":
                        os.path.basename(
                            ndvi_file
                        )
                },

                "true_color": {

                    "filename":
                        os.path.basename(
                            true_color_file
                        )
                }
            },

            "message":
                "Live Sentinel-2 satellite imagery analyzed successfully using the trained drought model."
        })

    except KeyError as error:

        return jsonify({

            "success":
                False,

            "error":
                f"Missing required field: {error}"
        }), 400

    except ValueError as error:

        return jsonify({

            "success":
                False,

            "error":
                f"Invalid location value: {error}"
        }), 400

    except Exception as error:

        print(
            "Location analysis error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# IMAGE UPLOAD ANALYSIS
# ============================================================

@app.route(
    "/analyze-image",
    methods=["POST"]
)
def analyze_image():

    try:

        if image_model is None:
            return jsonify({

                "success":
                    False,

                "error":
                    "Image drought model is not loaded."
            }), 500

        if image_scaler is None:
            return jsonify({

                "success":
                    False,

                "error":
                    "Image feature scaler is not loaded."
            }), 500

        uploaded_file = request.files.get(
            "image"
        )

        if uploaded_file is None:
            uploaded_file = request.files.get(
                "file"
            )

        if uploaded_file is None:
            return jsonify({

                "success":
                    False,

                "error":
                    "No image file was uploaded."
            }), 400

        file_bytes = uploaded_file.read()

        if len(file_bytes) == 0:
            return jsonify({

                "success":
                    False,

                "error":
                    "Uploaded file is empty."
            }), 400

        filename = (
            uploaded_file.filename.lower()
        )

        # ----------------------------------------------------
        # READ TIFF
        # ----------------------------------------------------

        if filename.endswith(
            (
                ".tif",
                ".tiff"
            )
        ):

            with rasterio.MemoryFile(
                file_bytes
            ) as memfile:

                with memfile.open() as dataset:

                    image = dataset.read().astype(
                        np.float64
                    )

        # ----------------------------------------------------
        # READ JPG / JPEG / PNG
        # ----------------------------------------------------

        else:

            from PIL import Image

            pil_image = Image.open(
                io.BytesIO(
                    file_bytes
                )
            )

            image = np.array(
                pil_image
            ).astype(
                np.float64
            )

            if image.ndim == 2:

                image = image[
                    np.newaxis,
                    :,
                    :
                ]

            elif image.ndim == 3:

                image = np.transpose(
                    image,
                    (
                        2,
                        0,
                        1
                    )
                )

        # ----------------------------------------------------
        # EXTRACT FEATURES
        # ----------------------------------------------------

        image_features = (
            extract_uploaded_image_features(
                image
            )
        )

        # ----------------------------------------------------
        # SCALE FEATURES
        # ----------------------------------------------------

        scaled_features = (
            image_scaler.transform(
                image_features
            )
        )

        # ----------------------------------------------------
        # PREDICT
        # ----------------------------------------------------

        prediction = image_model.predict(
            scaled_features
        )

        predicted_class = str(
            prediction[0]
        )

        # ----------------------------------------------------
        # PROBABILITIES
        # ----------------------------------------------------

        probabilities = {}

        if hasattr(
            image_model,
            "predict_proba"
        ):

            probability_values = (
                image_model.predict_proba(
                    scaled_features
                )[0]
            )

            classes = image_model.classes_

            for class_name, probability in zip(
                classes,
                probability_values
            ):

                probabilities[
                    str(class_name)
                ] = round(
                    float(probability) * 100,
                    2
                )

        confidence = probabilities.get(
            predicted_class,
            None
        )

        # ----------------------------------------------------
        # IMAGE STATISTICS
        # ----------------------------------------------------

        mean_value = float(
            np.mean(image)
        )

        std_value = float(
            np.std(image)
        )

        min_value = float(
            np.min(image)
        )

        max_value = float(
            np.max(image)
        )

        median_value = float(
            np.median(image)
        )

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "mode":
                "image",

            "filename":
                uploaded_file.filename,

            "prediction":
                predicted_class,

            "predicted_severity":
                predicted_class,

            "confidence":
                confidence,

            "probabilities":
                probabilities,

            "image_features": {

                "mean":
                    round(
                        mean_value,
                        4
                    ),

                "standard_deviation":
                    round(
                        std_value,
                        4
                    ),

                "minimum":
                    round(
                        min_value,
                        4
                    ),

                "maximum":
                    round(
                        max_value,
                        4
                    ),

                "median":
                    round(
                        median_value,
                        4
                    )
            },

            "message":
                "Satellite image analyzed successfully using the trained image drought model."
        })

    except Exception as error:

        print(
            "Image analysis error:",
            error
        )

        return jsonify({

            "success":
                False,

            "error":
                str(error)
        }), 500


# ============================================================
# END OF LIVE LOCATION + IMAGE ANALYSIS
# ============================================================

# ============================================================
# VERSION 2 — LIVE NDVI API
# ============================================================

@app.route(
    "/live-ndvi",
    methods=["GET"]
)
def live_ndvi():

    try:

        result = read_ndvi_image()


        statistics = result[
            "statistics"
        ]


        return jsonify({

            "success":
                True,

            "filename":
                os.path.basename(
                    result["file_path"]
                ),

            "statistics":
                statistics,

            "metadata":
                result["metadata"]

        })


    except Exception as error:

        print(
            "Live NDVI error:",
            error
        )


        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500



# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================================="
    )

    print(
        " Drought Severity Mapping"
    )

    print(
        " Flask Server Starting..."
    )

    print(
        "=============================================="
    )

    print(
        f"Dataset records: "
        f"{len(prediction_df)}"
    )

    print(
        f"Original model loaded: "
        f"{model is not None}"
    )

    print(
        f"Original scaler loaded: "
        f"{scaler is not None}"
    )

    print(
        f"Image model loaded: "
        f"{image_model is not None}"
    )

    print(
        f"Image scaler loaded: "
        f"{image_scaler is not None}"
    )

    print(
        "==============================================\n"
    )


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )