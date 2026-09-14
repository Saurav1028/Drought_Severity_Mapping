# 🌾 Drought Severity Mapping

## AI-Based Drought Severity Prediction and Monitoring System

---

## 1. Project Overview

Drought Severity Mapping is an AI-based remote sensing and machine learning system designed to analyze environmental and satellite-derived information and classify drought severity at different geographical locations.

The system combines:

- Sentinel-2 satellite imagery
- Sentinel-1 SAR imagery
- NDVI information
- RGB imagery
- SAR VV information
- SAR VH information
- Vegetation percentage
- Water percentage
- Cloudiness
- Geographic coordinates
- Temporal information

The trained machine learning model classifies a location into one of four drought severity categories:

- Low
- Moderate
- Severe
- Extreme

The results are presented through an interactive web application developed using Flask, HTML, CSS and JavaScript.

---

# 2. Problem Statement

Drought can significantly affect agriculture, water resources, vegetation and ecosystems.

Traditional drought assessment can require large amounts of environmental observations and manual analysis.

This project aims to develop an automated system that combines remote sensing data and machine learning to provide drought severity predictions for multiple geographical locations.

---

# 3. Objectives

The main objectives of the project are:

1. Collect and organize satellite and environmental data.
2. Process remote sensing imagery.
3. Extract meaningful features from satellite imagery.
4. Combine satellite-derived features with environmental and temporal information.
5. Prepare the features for machine learning.
6. Train a drought severity classification model.
7. Generate drought severity predictions.
8. Visualize drought conditions geographically.
9. Provide satellite-image visualization.
10. Develop an interactive web-based drought monitoring system.

---

# 4. Dataset

The project contains data for 1,100 geographical records.

The dataset contains information such as:

- Record ID
- Latitude
- Longitude
- Year
- Month
- Cloudiness
- Water percentage
- Vegetation percentage
- NDVI
- Satellite imagery

The project also contains satellite imagery in TIFF format.

The imagery includes:

- NDVI
- RGB
- SAR VV
- SAR VH

---

# 5. Remote Sensing Features

## NDVI

NDVI stands for Normalized Difference Vegetation Index.

It is used to represent vegetation conditions.

The project uses NDVI information from two periods:

- NDVI Mean A
- NDVI Std A
- NDVI Mean B
- NDVI Std B

The difference between the two periods can help indicate changes in vegetation conditions.

---

## RGB

RGB imagery represents visible-spectrum information using:

- Red
- Green
- Blue

The project extracts:

- RGB Mean A
- RGB Std A
- RGB Mean B
- RGB Std B

---

## SAR VV

VV represents vertically transmitted and vertically received radar polarization.

The project extracts:

- VV Mean A
- VV Std A
- VV Mean B
- VV Std B

---

## SAR VH

VH represents vertically transmitted and horizontally received radar polarization.

The project extracts:

- VH Mean A
- VH Std A
- VH Mean B
- VH Std B

---

# 6. Feature Engineering

The machine learning system uses environmental, geographical, temporal and satellite-derived features.

The final prediction pipeline uses 24 features:

1. Latitud
2. Longitudes
3. Cloudiness Mean
4. Water percentage Mean
5. Vegetation percentage Mean
6. Year
7. Month
8. Duration_Days
9. NDVI_Mean_A
10. NDVI_Std_A
11. RGB_Mean_A
12. RGB_Std_A
13. VV_Mean_A
14. VV_Std_A
15. VH_Mean_A
16. VH_Std_A
17. NDVI_Mean_B
18. NDVI_Std_B
19. RGB_Mean_B
20. RGB_Std_B
21. VV_Mean_B
22. VV_Std_B
23. VH_Mean_B
24. VH_Std_B

---

# 7. Machine Learning Pipeline

The prediction pipeline follows:

```text
Raw Data
   ↓
Data Processing
   ↓
Satellite Feature Extraction
   ↓
Feature Engineering
   ↓
Feature Scaling
   ↓
Trained Machine Learning Model
   ↓
Drought Severity Prediction