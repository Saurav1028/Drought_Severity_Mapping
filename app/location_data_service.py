# ============================================================
# LIVE SATELLITE DATA SERVICE
# ============================================================

import os

import numpy as np
import rasterio
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# LIVE NDVI FOLDER
# ============================================================

LIVE_NDVI_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "live_satellite",
    "ndvi"
)


# ============================================================
# FIND LATEST NDVI FILE
# ============================================================

def find_latest_ndvi():

    if not os.path.exists(
        LIVE_NDVI_FOLDER
    ):

        raise FileNotFoundError(
            "Live NDVI folder not found:\n"
            + LIVE_NDVI_FOLDER
        )


    files = [

        file_name

        for file_name in os.listdir(
            LIVE_NDVI_FOLDER
        )

        if file_name.lower().endswith(
            (
                ".tif",
                ".tiff"
            )
        )

    ]


    if not files:

        raise FileNotFoundError(
            "No NDVI TIFF file found in:\n"
            + LIVE_NDVI_FOLDER
        )


    files.sort(

        key=lambda file_name:
            os.path.getmtime(

                os.path.join(
                    LIVE_NDVI_FOLDER,
                    file_name
                )

            ),

        reverse=True

    )


    return os.path.join(

        LIVE_NDVI_FOLDER,

        files[0]

    )


# ============================================================
# READ NDVI IMAGE
# ============================================================

def read_ndvi_image(
    file_path=None
):

    if file_path is None:

        file_path = find_latest_ndvi()


    if not os.path.exists(
        file_path
    ):

        raise FileNotFoundError(
            "NDVI file not found:\n"
            + file_path
        )


    with rasterio.open(
        file_path
    ) as dataset:

        image = dataset.read(
            1
        ).astype(
            np.float64
        )


        metadata = {

            "width":
                dataset.width,

            "height":
                dataset.height,

            "crs":
                str(dataset.crs),

            "transform":
                str(dataset.transform)

        }


    # ========================================================
    # REMOVE INVALID VALUES
    # ========================================================

    valid_pixels = image[
        np.isfinite(image)
    ]


    if valid_pixels.size == 0:

        raise ValueError(
            "The NDVI image does not contain valid pixels."
        )


    # ========================================================
    # CALCULATE NDVI STATISTICS
    # ========================================================

    statistics = {

        "mean":
            float(
                np.mean(
                    valid_pixels
                )
            ),

        "standard_deviation":
            float(
                np.std(
                    valid_pixels
                )
            ),

        "minimum":
            float(
                np.min(
                    valid_pixels
                )
            ),

        "maximum":
            float(
                np.max(
                    valid_pixels
                )
            ),

        "median":
            float(
                np.median(
                    valid_pixels
                )
            ),

        "valid_pixels":
            int(
                valid_pixels.size
            )

    }


    return {

        "file_path":
            file_path,

        "metadata":
            metadata,

        "statistics":
            statistics

    }

# ============================================================
# CREATE AOI FROM ANY LOCATION
# ============================================================

def create_location_bbox(
    latitude,
    longitude,
    size_degrees=0.05
):

    latitude = float(latitude)
    longitude = float(longitude)

    if latitude < -90 or latitude > 90:

        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if longitude < -180 or longitude > 180:

        raise ValueError(
            "Longitude must be between -180 and 180."
        )

    half_size = size_degrees / 2

    min_longitude = longitude - half_size
    min_latitude = latitude - half_size

    max_longitude = longitude + half_size
    max_latitude = latitude + half_size

    min_longitude = max(
        -180,
        min_longitude
    )

    max_longitude = min(
        180,
        max_longitude
    )

    min_latitude = max(
        -90,
        min_latitude
    )

    max_latitude = min(
        90,
        max_latitude
    )

    return [
        min_longitude,
        min_latitude,
        max_longitude,
        max_latitude
    ]

# ============================================================
# REQUEST NDVI FROM SENTINEL HUB
# ============================================================

def request_ndvi_for_location(
    latitude,
    longitude,
    start_date,
    end_date
):

    # --------------------------------------------------------
    # Create an area around the requested location
    # --------------------------------------------------------

    bbox = create_location_bbox(
        latitude,
        longitude
    )


    # --------------------------------------------------------
    # Get Sentinel Hub access token
    # --------------------------------------------------------

    access_token = (
        get_sentinel_access_token()
    )


    # --------------------------------------------------------
    # Sentinel Hub Process API
    # --------------------------------------------------------

    process_url = (
        "https://services.sentinel-hub.com/"
        "api/v1/process"
    )


    # --------------------------------------------------------
    # NDVI Evalscript
    # --------------------------------------------------------

    evalscript = """
//VERSION=3

function setup() {

    return {

        input: [
            "B04",
            "B08"
        ],

        output: {

            bands: 1,

            sampleType: "FLOAT32"

        }

    };

}


function evaluatePixel(sample) {

    let denominator =
        sample.B08 + sample.B04;

    if (denominator === 0) {

        return [0];

    }

    let ndvi =
        (sample.B08 - sample.B04)
        / denominator;

    return [ndvi];

}
"""


    # --------------------------------------------------------
    # Request body
    # --------------------------------------------------------

    request_body = {

        "input": {

            "bounds": {

                "bbox": bbox,

                "properties": {

                    "crs":
                        "http://www.opengis.net/def/crs/EPSG/0/4326"

                }

            },

            "data": [

                {

                    "type":
                        "sentinel-2-l2a",

                    "dataFilter": {

                        "timeRange": {

                            "from":
                                start_date
                                + "T00:00:00Z",

                            "to":
                                end_date
                                + "T23:59:59Z"

                        },

                        "mosaickingOrder":
                            "mostRecent"

                    },

                    "processing": {

                        "upsampling":
                            "BILINEAR",

                        "downsampling":
                            "BILINEAR"

                    }

                }

            ]

        },

        "output": {

            "width": 256,

            "height": 256,

            "responses": [

                {

                    "identifier":
                        "default",

                    "format": {

                        "type":
                            "image/tiff"

                    }

                }

            ]

        },

        "evalscript":
            evalscript

    }


    # --------------------------------------------------------
    # Send request
    # --------------------------------------------------------

    response = requests.post(

        process_url,

        headers={

            "Authorization":
                "Bearer "
                + access_token,

            "Content-Type":
                "application/json"

        },

        json=request_body,

        timeout=120

    )


    # --------------------------------------------------------
    # Check response
    # --------------------------------------------------------

    if response.status_code != 200:

        raise RuntimeError(

            "Sentinel Hub NDVI request failed: "

            + str(response.status_code)

            + "\n"

            + response.text

        )


       # --------------------------------------------------------
    # SAVE NDVI TIFF AUTOMATICALLY
    # --------------------------------------------------------

    os.makedirs(
        LIVE_NDVI_FOLDER,
        exist_ok=True
    )

    output_filename = (
        f"ndvi_"
        f"{float(latitude):.6f}_"
        f"{float(longitude):.6f}_"
        f"{start_date}_"
        f"{end_date}.tiff"
    )

    output_path = os.path.join(
        LIVE_NDVI_FOLDER,
        output_filename
    )

    with open(
        output_path,
        "wb"
    ) as output_file:

        output_file.write(
            response.content
        )

    print(
        "✓ NDVI TIFF saved:"
    )

    print(
        output_path
    )

    return output_path






# ============================================================
# SENTINEL HUB AUTHENTICATION
# ============================================================

def get_sentinel_access_token():

    client_id = os.getenv(
        "SH_CLIENT_ID"
    )

    client_secret = os.getenv(
        "SH_CLIENT_SECRET"
    )


    if not client_id:

        raise ValueError(
            "SH_CLIENT_ID is missing from .env"
        )


    if not client_secret:

        raise ValueError(
            "SH_CLIENT_SECRET is missing from .env"
        )


    token_url = (
    "https://services.sentinel-hub.com/"
    "auth/realms/main/protocol/openid-connect/token"
)


    response = requests.post(

        token_url,

        data={

            "grant_type":
                "client_credentials",

            "client_id":
                client_id,

            "client_secret":
                client_secret

        },

        timeout=30

    )


    if response.status_code != 200:

        raise RuntimeError(

            "Sentinel Hub authentication failed: "

            + response.text

        )


    token_data = response.json()


    access_token = token_data.get(
        "access_token"
    )


    if not access_token:

        raise RuntimeError(
            "Authentication succeeded but "
            "no access token was returned."
        )


    return access_token


# ============================================================
# SENTINEL HUB AUTHENTICATION TEST
# ============================================================

def test_sentinel_authentication():

    print()

    print(
        "=" * 60
    )

    print(
        "SENTINEL HUB AUTHENTICATION TEST"
    )

    print(
        "=" * 60
    )


    access_token = (
        get_sentinel_access_token()
    )


    if access_token:

        print(
            "✓ Credentials accepted."
        )

        print(
            "✓ Access token received."
        )

        print(
            "✓ Sentinel Hub connection successful."
        )


    print(
        "=" * 60
    )


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    try:

        test_sentinel_authentication()

    except Exception as error:

        print()

        print(
            "❌ Sentinel Hub authentication error:"
        )

        print(
            error
        )


# ============================================================
# TEST ANY-LOCATION NDVI REQUEST + SAVED TIFF
# ============================================================

def test_any_location_ndvi():

    latitude = 20.296100
    longitude = 85.824500

    start_date = "2025-08-01"
    end_date = "2025-08-31"


    print()
    print("=" * 60)
    print("ANY-LOCATION NDVI + TIFF TEST")
    print("=" * 60)

    print(
        f"Latitude: {latitude}"
    )

    print(
        f"Longitude: {longitude}"
    )

    print(
        f"Date range: {start_date} to {end_date}"
    )

    print()
    print(
        "Requesting NDVI from Sentinel Hub..."
    )


    # --------------------------------------------------------
    # REQUEST AND SAVE TIFF
    # --------------------------------------------------------

    output_path = request_ndvi_for_location(

        latitude=latitude,

        longitude=longitude,

        start_date=start_date,

        end_date=end_date

    )


    print()
    print(
        "✓ NDVI TIFF returned and saved."
    )

    print(
        f"File: {output_path}"
    )


    # --------------------------------------------------------
    # VERIFY FILE EXISTS
    # --------------------------------------------------------

    if not os.path.exists(
        output_path
    ):

        raise FileNotFoundError(
            "The NDVI TIFF was not created."
        )


    file_size = os.path.getsize(
        output_path
    )


    print()
    print(
        f"✓ File exists."
    )

    print(
        f"File size: {file_size} bytes"
    )


    # --------------------------------------------------------
    # READ SAVED TIFF
    # --------------------------------------------------------

    print()
    print(
        "Opening saved TIFF with Rasterio..."
    )


    result = read_ndvi_image(
        output_path
    )


    # --------------------------------------------------------
    # DISPLAY STATISTICS
    # --------------------------------------------------------

    statistics = result[
        "statistics"
    ]


    print()
    print(
        "✓ TIFF opened successfully."
    )

    print()
    print(
        "NDVI Statistics:"
    )


    for key, value in statistics.items():

        print(
            f"{key}: {value}"
        )


    print()
    print("=" * 60)
    print(
        "✓ AUTOMATIC NDVI PIPELINE VERIFIED"
    )
    print("=" * 60)


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    try:

        test_any_location_ndvi()

    except Exception as error:

        print()
        print("=" * 60)
        print(
            "❌ AUTOMATIC NDVI PIPELINE FAILED"
        )
        print("=" * 60)

        print(
            error
        )

        print("=" * 60)



# ============================================================
# TEST ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        test_any_location_ndvi()

    except Exception as error:

        print()
        print("=" * 60)
        print("❌ ANY-LOCATION NDVI TEST FAILED")
        print("=" * 60)

        print(error)

        print("=" * 60)

# ============================================================
# REQUEST TRUE-COLOR SATELLITE IMAGE
# ============================================================

def request_true_color_for_location(
    latitude,
    longitude,
    start_date,
    end_date
):

    # Create bounding box
    bbox = create_location_bbox(
        latitude,
        longitude
    )

    # Get Sentinel Hub token
    access_token = get_sentinel_access_token()

    # Sentinel Hub Process API
    process_url = (
        "https://services.sentinel-hub.com/"
        "api/v1/process"
    )

    # True-color RGB
    evalscript = """
//VERSION=3

function setup() {

    return {

        input: [
            "B02",
            "B03",
            "B04"
        ],

        output: {

            bands: 3,

            sampleType: "UINT8"

        }

    };

}

function evaluatePixel(sample) {

    return [

        Math.min(255, Math.max(0, 255 * 2.5 * sample.B04)),
        Math.min(255, Math.max(0, 255 * 2.5 * sample.B03)),
        Math.min(255, Math.max(0, 255 * 2.5 * sample.B02))

    ];

}
"""

    # Request body
    request_body = {

        "input": {

            "bounds": {

                "bbox": bbox,

                "properties": {

                    "crs":
                        "http://www.opengis.net/def/crs/EPSG/0/4326"

                }

            },

            "data": [

                {

                    "type":
                        "sentinel-2-l2a",

                    "dataFilter": {

                        "timeRange": {

                            "from":
                                start_date
                                + "T00:00:00Z",

                            "to":
                                end_date
                                + "T23:59:59Z"

                        },

                        "mosaickingOrder":
                            "mostRecent"

                    }

                }

            ]

        },

        "output": {

            "width": 1024,

            "height": 1024,

            "responses": [

                {

                    "identifier":
                        "default",

                    "format": {

                        "type":
                            "image/png"

                    }

                }

            ]

        },

        "evalscript":
            evalscript

    }

    # Send request
    response = requests.post(

        process_url,

        headers={

            "Authorization":
                "Bearer "
                + access_token,

            "Content-Type":
                "application/json"

        },

        json=request_body,

        timeout=120

    )

    # Check response
    if response.status_code != 200:

        raise RuntimeError(

            "Sentinel Hub true-color request failed: "

            + str(response.status_code)

            + "\n"

            + response.text

        )

    # Create output folder
    true_color_folder = os.path.join(

        BASE_DIR,

        "data",

        "live_satellite",

        "true_color"

    )

    os.makedirs(

        true_color_folder,

        exist_ok=True

    )

    # File name
    output_filename = (

        f"true_color_"

        f"{float(latitude):.6f}_"

        f"{float(longitude):.6f}_"

        f"{start_date}_"

        f"{end_date}.png"

    )

    output_path = os.path.join(

        true_color_folder,

        output_filename

    )

    # Save image
    with open(

        output_path,

        "wb"

    ) as output_file:

        output_file.write(

            response.content

        )

    print()

    print(
        "✓ True-color satellite image saved:"
    )

    print(
        output_path
    )

    return output_path 

# ============================================================
# TEST TRUE-COLOR SATELLITE IMAGE
# ============================================================

def test_true_color():

    latitude = 20.296100
    longitude = 85.824500

    start_date = "2025-08-01"
    end_date = "2025-08-31"

    print()
    print("=" * 60)
    print("TRUE-COLOR SATELLITE IMAGE TEST")
    print("=" * 60)

    print(
        f"Latitude: {latitude}"
    )

    print(
        f"Longitude: {longitude}"
    )

    print(
        f"Date range: {start_date} to {end_date}"
    )

    print()
    print(
        "Requesting true-color satellite image..."
    )

    image_path = request_true_color_for_location(

        latitude=latitude,

        longitude=longitude,

        start_date=start_date,

        end_date=end_date

    )

    print()

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            "True-color image was not created."
        )

    file_size = os.path.getsize(
        image_path
    )

    print(
        "✓ True-color image created successfully."
    )

    print(
        f"File: {image_path}"
    )

    print(
        f"File size: {file_size} bytes"
    )

    print()
    print("=" * 60)
    print("✓ TRUE-COLOR SATELLITE TEST PASSED")
    print("=" * 60)


# ============================================================
# RUN TRUE-COLOR TEST
# ============================================================

if __name__ == "__main__":

    test_true_color()          