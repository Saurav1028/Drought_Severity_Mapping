// ============================================================
// DROUGHT SEVERITY MAPPING
// COMPLETE FRONTEND JAVASCRIPT
// VERSION 2
// ============================================================


// ============================================================
// GLOBAL VARIABLES
// ============================================================

let map = null;

let allLocations = [];

let mapMarkers = [];

let severityChartInstance = null;
let ndviChartInstance = null;
let vegetationChartInstance = null;
let yearlySeverityChartInstance = null;


// ============================================================
// PAGE INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", function () {

    console.log("Drought Severity Mapping application started.");

    if (typeof initializeMap === "function") {
        initializeMap();
    }

    if (typeof setupFilterListeners === "function") {
        setupFilterListeners();
    }

    if (typeof setupPredictionForm === "function") {
        setupPredictionForm();
    }

    if (typeof setupVersion2 === "function") {
        setupVersion2();
    }

    if (typeof loadDashboardStats === "function") {
        loadDashboardStats();
    }

    if (typeof loadLocations === "function") {
        loadLocations();
    }

    if (typeof loadAnalytics === "function") {
        loadAnalytics();
    }

});

// ============================================================
// INITIALIZE MAP
// ============================================================

function initializeMap() {

    const mapElement = document.getElementById("map");

    if (!mapElement) {
        console.warn("Map element not found.");
        return;
    }

    if (typeof L === "undefined") {
        console.error("Leaflet library is not loaded.");
        return;
    }

    map = L.map("map").setView([20, 0], 2);


    // ============================================================
    // STREET MAP
    // ============================================================


    // ============================================================
    // SATELLITE MAP LAYER
    // ============================================================

    const streetMapLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 22,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    );

    const satelliteLayer = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
            maxNativeZoom: 17,
            maxZoom: 22,
            attribution: "Tiles &copy; Esri"
        }
    );

    let lastValidZoom = map.getZoom();
    let zoomRecovery = false;

    function protectMapFromUnavailableTiles(layer) {

        layer.on("tileload", function () {
            if (!zoomRecovery) {
                lastValidZoom = map.getZoom();
            }
        });

        layer.on("tileerror", function () {

            if (zoomRecovery) {
                return;
            }

            const currentZoom = map.getZoom();

            if (currentZoom > 1) {

                zoomRecovery = true;

                map.setZoom(
                    Math.min(
                        lastValidZoom,
                        currentZoom - 1
                    ),
                    {
                        animate: true
                    }
                );

                setTimeout(function () {
                    zoomRecovery = false;
                }, 700);
            }
        });
    }

    protectMapFromUnavailableTiles(streetMapLayer);


    // ============================================================
    // SATELLITE / STREET MAP SWITCHER
    // ============================================================

    L.control.layers(
        {
            "Street Map": streetMapLayer,
            "Satellite": satelliteLayer
        },
        null,
        {
            position: "topright"
        }
    ).addTo(map);


    // ============================================================
    // DEFAULT SATELLITE VIEW
    // ============================================================

    streetMapLayer.addTo(map);
}

// ============================================================
// DASHBOARD STATISTICS
// ============================================================

async function loadDashboardStats() {

    try {

        const response = await fetch("/dashboard-stats");

        if (!response.ok) {
            throw new Error(
                "Server returned " + response.status
            );
        }

        const data = await response.json();

        setText("totalLocations", data.total_locations ?? 0);
        setText("lowCount", data.low ?? 0);
        setText("moderateCount", data.moderate ?? 0);
        setText("severeCount", data.severe ?? 0);
        setText("extremeCount", data.extreme ?? 0);

        setFormattedText(
            "averageNDVI",
            data.average_ndvi,
            4
        );

        setFormattedText(
            "averageVegetation",
            data.average_vegetation,
            2,
            "%"
        );

        setFormattedText(
            "averageWater",
            data.average_water,
            4
        );

    }
    catch (error) {

        console.error(
            "Dashboard statistics error:",
            error
        );

    }

}


// ============================================================
// LOAD LOCATIONS
// ============================================================

async function loadLocations() {

    try {

        const response = await fetch("/locations");

        if (!response.ok) {
            throw new Error(
                "Server returned " + response.status
            );
        }

        const locations = await response.json();

        if (!Array.isArray(locations)) {
            throw new Error(
                "Invalid location data received."
            );
        }

        allLocations = locations;

        displayLocations(allLocations);

        setupLocationSelector();

        updateMapRecordCount(allLocations.length);

        populateFilterOptions();

    }
    catch (error) {

        console.error(
            "Location loading error:",
            error
        );

    }

}


// ============================================================
// DISPLAY LOCATIONS ON MAP
// ============================================================

function displayLocations(locations) {

    if (!map) {
        return;
    }

    mapMarkers.forEach(function (marker) {

        map.removeLayer(marker);

    });

    mapMarkers = [];

    locations.forEach(function (location) {

        const marker = createSeverityMarker(location);

        if (marker) {

            marker.addTo(map);

            mapMarkers.push(marker);

        }

    });

}


// ============================================================
// CREATE MAP MARKER
// ============================================================

function createSeverityMarker(location) {

    if (
        !map ||
        location.latitude === undefined ||
        location.longitude === undefined
    ) {
        return null;
    }

    const color = getSeverityColor(
        location.prediction
    );

    const marker = L.circleMarker(
        [
            Number(location.latitude),
            Number(location.longitude)
        ],
        {
            radius: 7,
            fillColor: color,
            color: "#ffffff",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.85
        }
    );

    marker.bindPopup(

        "<strong>📍 Location " +
        location.id +
        "</strong>" +

        "<br><br>" +

        "Latitude: " +
        Number(location.latitude).toFixed(6) +

        "<br>" +

        "Longitude: " +
        Number(location.longitude).toFixed(6) +

        "<br>" +

        "Year: " +
        location.year +

        "<br>" +

        "Month: " +
        location.month +

        "<br><br>" +

        "<strong>🌾 Drought Severity: " +
        location.prediction +
        "</strong>" +

        "<br><br>" +

        "<button onclick=\"selectLocation(" +
        location.id +
        ")\">" +

        "🔍 Analyze Location" +

        "</button>"

    );

    return marker;

}


// ============================================================
// SEVERITY COLOR
// ============================================================

function getSeverityColor(severity) {

    switch (
    String(severity).toLowerCase()
    ) {

        case "low":
            return "#2e7d32";

        case "moderate":
            return "#f9a825";

        case "severe":
            return "#ef6c00";

        case "extreme":
            return "#c62828";

        default:
            return "#555555";

    }

}


// ============================================================
// MAP LEGEND
// ============================================================

function addMapLegend() {

    if (!map) {
        return;
    }

    const legend = L.control({
        position: "bottomright"
    });

    legend.onAdd = function () {

        const div = L.DomUtil.create(
            "div",
            "map-legend"
        );

        div.innerHTML =

            "<h4>Drought Severity</h4>" +

            "<div>" +
            "<span class='legend-dot low'></span>" +
            " Low" +
            "</div>" +

            "<div>" +
            "<span class='legend-dot moderate'></span>" +
            " Moderate" +
            "</div>" +

            "<div>" +
            "<span class='legend-dot severe'></span>" +
            " Severe" +
            "</div>" +

            "<div>" +
            "<span class='legend-dot extreme'></span>" +
            " Extreme" +
            "</div>";

        return div;

    };

    legend.addTo(map);

}


// ============================================================
// FILTER LISTENERS
// ============================================================

function setupFilterListeners() {

    const yearFilter =
        document.getElementById("yearFilter");

    const monthFilter =
        document.getElementById("monthFilter");

    const severityFilter =
        document.getElementById("severityFilter");

    if (yearFilter) {

        yearFilter.addEventListener(
            "change",
            applyMapFilters
        );

    }

    if (monthFilter) {

        monthFilter.addEventListener(
            "change",
            applyMapFilters
        );

    }

    if (severityFilter) {

        severityFilter.addEventListener(
            "change",
            applyMapFilters
        );

    }

    const resetButton =
        document.getElementById("resetFiltersBtn");

    if (resetButton) {

        resetButton.addEventListener(
            "click",
            resetMapFilters
        );

    }

}

// ============================================================
// POPULATE FILTER OPTIONS
// ============================================================

function populateFilterOptions() {

    const yearFilter =
        document.getElementById("yearFilter");

    const monthFilter =
        document.getElementById("monthFilter");


    // ========================================================
    // YEAR FILTER
    // ========================================================

    if (yearFilter) {

        const years = [
            ...new Set(
                allLocations.map(
                    location => location.year
                )
            )
        ].sort();

        yearFilter.innerHTML =
            "<option value='all'>All</option>";

        years.forEach(function (year) {

            const option =
                document.createElement("option");

            option.value = year;
            option.textContent = year;

            yearFilter.appendChild(option);

        });

    }


    // ========================================================
    // MONTH FILTER
    // ========================================================

    if (monthFilter) {

        const months = [
            { value: 1, name: "Jan" },
            { value: 2, name: "Feb" },
            { value: 3, name: "Mar" },
            { value: 4, name: "Apr" },
            { value: 5, name: "May" },
            { value: 6, name: "Jun" },
            { value: 7, name: "Jul" },
            { value: 8, name: "Aug" },
            { value: 9, name: "Sep" },
            { value: 10, name: "Oct" },
            { value: 11, name: "Nov" },
            { value: 12, name: "Dec" }
        ];

        monthFilter.innerHTML =
            "<option value='all'>All</option>";

        months.forEach(function (month) {

            const option =
                document.createElement("option");

            option.value = month.value;
            option.textContent = month.name;

            monthFilter.appendChild(option);

        });

    }

}


// ============================================================
// APPLY MAP FILTERS
// ============================================================

function applyMapFilters() {

    const year =
        document.getElementById("yearFilter")?.value
        || "all";

    const month =
        document.getElementById("monthFilter")?.value
        || "all";

    const severity =
        document.getElementById("severityFilter")?.value
        || "all";


    const filtered =
        allLocations.filter(function (location) {

            const yearMatch =
                year === "all" ||
                String(location.year) === String(year);

            const monthMatch =
                month === "all" ||
                String(location.month) === String(month);

            const severityMatch =
                severity === "all" ||
                String(location.prediction) === severity;

            return (
                yearMatch &&
                monthMatch &&
                severityMatch
            );

        });


    displayLocations(filtered);

    updateMapRecordCount(filtered.length);

}


// ============================================================
// RESET MAP FILTERS
// ============================================================

function resetMapFilters() {

    const yearFilter =
        document.getElementById("yearFilter");

    const monthFilter =
        document.getElementById("monthFilter");

    const severityFilter =
        document.getElementById("severityFilter");


    if (yearFilter) {
        yearFilter.value = "all";
    }

    if (monthFilter) {
        monthFilter.value = "all";
    }

    if (severityFilter) {
        severityFilter.value = "all";
    }


    displayLocations(allLocations);

    updateMapRecordCount(
        allLocations.length
    );

}


// ============================================================
// MAP RECORD COUNT
// ============================================================

function updateMapRecordCount(count) {

    setText(
        "mapRecordCount",
        count
    );

}


// ============================================================
// LOCATION SELECTOR
// ============================================================

function setupLocationSelector() {

    const select =
        document.getElementById("recordSelect")
        ||
        document.getElementById("record_id");

    const search =
        document.getElementById("locationSearch");


    if (!select) {
        return;
    }


    populateLocationDropdown(
        allLocations
    );


    if (
        select.dataset.initialized === "true"
    ) {
        return;
    }


    select.dataset.initialized = "true";


    select.addEventListener(
        "change",
        function () {

            const recordId =
                select.value;

            if (recordId === "") {
                return;
            }

            updateLocationInfo(
                Number(recordId)
            );

        }
    );


    if (search) {

        search.addEventListener(
            "input",
            function () {

                filterLocationOptions(
                    search.value
                );

            }
        );

    }

}


// ============================================================
// POPULATE LOCATION DROPDOWN
// ============================================================

function populateLocationDropdown(locations) {

    const select =
        document.getElementById("recordSelect")
        ||
        document.getElementById("record_id");


    if (!select) {
        return;
    }


    select.innerHTML =
        "<option value=''>" +
        "-- Select a location --" +
        "</option>";


    locations.forEach(function (location) {

        const option =
            document.createElement("option");


        option.value =
            location.id;


        option.textContent =

            "Record " +
            location.id +

            " | " +

            Number(
                location.latitude
            ).toFixed(4) +

            ", " +

            Number(
                location.longitude
            ).toFixed(4) +

            " | " +

            location.prediction;


        select.appendChild(option);

    });

}


// ============================================================
// FILTER LOCATION OPTIONS
// ============================================================

function filterLocationOptions(searchText) {

    const text =
        String(searchText)
            .trim()
            .toLowerCase();


    const filtered =
        allLocations.filter(function (location) {

            return (

                String(location.id)
                    .toLowerCase()
                    .includes(text)

                ||

                String(location.latitude)
                    .toLowerCase()
                    .includes(text)

                ||

                String(location.longitude)
                    .toLowerCase()
                    .includes(text)

                ||

                String(location.prediction)
                    .toLowerCase()
                    .includes(text)

            );

        });


    populateLocationDropdown(
        filtered
    );

}


// ============================================================
// UPDATE LOCATION INFORMATION
// ============================================================

function updateLocationInfo(recordId) {

    const info =
        document.getElementById("selectedLocationInfo")
        ||
        document.getElementById("locationInfo");


    if (!info) {
        return;
    }


    const location =
        allLocations.find(function (item) {

            return Number(item.id) ===
                Number(recordId);

        });


    if (!location) {

        info.innerHTML =
            "❌ Location not found.";

        return;

    }


    info.innerHTML =

        "<strong>📍 Record " +
        location.id +
        "</strong>" +

        "<br><br>" +

        "Latitude: " +
        Number(
            location.latitude
        ).toFixed(6) +

        "<br>" +

        "Longitude: " +
        Number(
            location.longitude
        ).toFixed(6) +

        "<br>" +

        "Year: " +
        location.year +

        "<br>" +

        "Month: " +
        location.month +

        "<br><br>" +

        "Current classification: " +

        "<strong>" +
        location.prediction +
        "</strong>";

}


// ============================================================
// SELECT LOCATION FROM MAP
// ============================================================

function selectLocation(recordId) {

    const select =
        document.getElementById("recordSelect")
        ||
        document.getElementById("record_id");


    if (select) {

        select.value =
            recordId;

    }


    updateLocationInfo(
        recordId
    );

    analyzeRecord(
        recordId
    );


    const section =
        document.getElementById("predictionResult")
        ||
        document.querySelector(
            ".prediction-section"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

    }

}


// ============================================================
// PREDICTION FORM
// ============================================================

function setupPredictionForm() {

    const form =
        document.getElementById(
            "predictionForm"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();


            const select =
                document.getElementById(
                    "recordSelect"
                )
                ||
                document.getElementById(
                    "record_id"
                );


            if (!select || select.value === "") {

                setHTML(
                    "result",
                    "❌ Please select a location first."
                );

                return;

            }


            analyzeRecord(
                Number(select.value)
            );

        }
    );

}


// ============================================================
// ANALYZE EXISTING RECORD
// ============================================================

async function analyzeRecord(recordId) {

    const result =
        document.getElementById("result");

    const loading =
        document.getElementById("loading");


    if (loading) {

        loading.innerHTML =
            "⏳ Analyzing location...";

    }


    if (result) {

        result.innerHTML =
            "⏳ Processing Location " +
            recordId +
            "...";

    }


    loadSatelliteImages(
        recordId
    );

    const selectedLocation = allLocations.find(
        location => Number(location.id) === Number(recordId)
    );

    if (selectedLocation && map) {
        map.flyTo(
            [
                Number(selectedLocation.latitude),
                Number(selectedLocation.longitude)
            ],
            10,
            {
                animate: true,
                duration: 1.2
            }
        );
    }

    if (window.requestedLocationMarker) {
        map.removeLayer(window.requestedLocationMarker);
    }

    window.requestedLocationMarker = L.marker([
        Number(selectedLocation.latitude),
        Number(selectedLocation.longitude)
    ])
        .addTo(map)
        .bindPopup(
            "<strong>Selected Dataset Location</strong><br>" +
            "Latitude: " + selectedLocation.latitude +
            "<br>Longitude: " + selectedLocation.longitude
        )
        .openPopup();


    try {

        const response =
            await fetch(
                "/predict-record",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        record_id:
                            Number(recordId)
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                "Prediction server returned " +
                response.status
            );

        }


        const data =
            await response.json();

        updateEnvironmentalIndicators(data);


        if (data.error) {

            throw new Error(
                data.error
            );

        }


        const severity =
            data.prediction;


        if (result) {

            result.innerHTML =

                "<div class='prediction-result'>" +

                "<h2>🌾 Predicted Drought Severity</h2>" +

                "<h1 class='severity-" +

                String(
                    severity
                ).toLowerCase() +

                "'>" +

                severity +

                "</h1>" +

                "<p>" +

                "<strong>Dataset Record:</strong> " +

                data.record_id +

                "</p>" +

                "</div>";

        }


        updateEnvironmentalIndicators(
            data
        );


        createDroughtAssessment(
            data,
            severity
        );


        if (loading) {

            loading.innerHTML =
                "✅ Analysis completed successfully.";

        }

    }
    catch (error) {

        console.error(
            "Prediction error:",
            error
        );


        if (loading) {
            loading.innerHTML = "";
        }


        if (result) {

            result.innerHTML =
                "❌ Error: " +
                error.message;

        }

    }

}


// ============================================================
// ENVIRONMENTAL INDICATORS
// ============================================================

function updateEnvironmentalIndicators(data) {

    setFormattedText(
        "indicatorLatitude",
        data.latitude,
        6
    );

    setFormattedText(
        "indicatorLongitude",
        data.longitude,
        6
    );

    setText(
        "indicatorYear",
        data.year ?? "—"
    );

    setText(
        "indicatorMonth",
        data.month ?? "—"
    );

    setFormattedText(
        "indicatorNDVI",
        data.ndvi_A,
        4
    );

    setFormattedText(
        "indicatorVegetation",
        data.vegetation_percentage,
        2,
        "%"
    );

    setFormattedText(
        "indicatorWater",
        data.water_percentage,
        4
    );

    setFormattedText(
        "indicatorCloudiness",
        data.cloudiness,
        4
    );

}


// ============================================================
// SATELLITE IMAGE LOADING
// ============================================================

function loadSatelliteImages(recordId) {

    const imageURLs = {

        ndviImageA:
            "/satellite/ndvi/" +
            recordId +
            "/A",

        ndviImageB:
            "/satellite/ndvi/" +
            recordId +
            "/B",

        rgbImageA:
            "/satellite/rgb/" +
            recordId +
            "/A",

        rgbImageB:
            "/satellite/rgb/" +
            recordId +
            "/B",

        vvImageA:
            "/satellite/vv/" +
            recordId +
            "/A",

        vvImageB:
            "/satellite/vv/" +
            recordId +
            "/B",

        vhImageA:
            "/satellite/vh/" +
            recordId +
            "/A",

        vhImageB:
            "/satellite/vh/" +
            recordId +
            "/B"

    };


    Object.entries(
        imageURLs
    ).forEach(
        function ([id, url]) {

            const image =
                document.getElementById(id);


            if (!image) {

                console.warn(
                    "Image element not found:",
                    id
                );

                return;

            }


            image.onload =
                function () {

                    image.style.display =
                        "block";

                };


            image.onerror =
                function () {

                    console.error(
                        "Satellite image failed:",
                        url
                    );

                    image.style.display =
                        "none";

                };


            image.src =
                url +
                "?t=" +
                Date.now();

        }
    );


    const satelliteStatus =
        document.getElementById(
            "satelliteStatus"
        );


    if (satelliteStatus) {

        satelliteStatus.innerHTML =
            "⏳ Loading satellite imagery for Record " +
            recordId +
            "...";

    }

}

// ============================================================
// DROUGHT ASSESSMENT
// ============================================================

function createDroughtAssessment(
    data,
    severity
) {

    const container =
        document.getElementById(
            "assessmentContent"
        )
        ||
        document.getElementById(
            "droughtAssessment"
        );


    if (!container) {
        return;
    }


    const ndviA =
        Number(data.ndvi_A);

    const ndviB =
        Number(data.ndvi_B);

    const vegetation =
        Number(data.vegetation_percentage);

    const water =
        Number(data.water_percentage);

    const cloudiness =
        Number(data.cloudiness);


    const ndviChange =
        Number.isFinite(ndviA) &&
            Number.isFinite(ndviB)
            ? ndviB - ndviA
            : NaN;


    let ndviStatus =
        "Not available";


    if (Number.isFinite(ndviChange)) {

        if (ndviChange > 0.05) {
            ndviStatus = "Strong increase";
        }

        else if (ndviChange > 0) {
            ndviStatus = "Slight increase";
        }

        else if (ndviChange < -0.05) {
            ndviStatus = "Strong decrease";
        }

        else if (ndviChange < 0) {
            ndviStatus = "Slight decrease";
        }

        else {
            ndviStatus =
                "No significant change";
        }

    }


    let assessmentText;


    switch (
    String(severity).toLowerCase()
    ) {

        case "low":

            assessmentText =
                "The model classified this location as Low drought severity.";

            break;


        case "moderate":

            assessmentText =
                "The model classified this location as Moderate drought severity.";

            break;


        case "severe":

            assessmentText =
                "The model classified this location as Severe drought severity.";

            break;


        case "extreme":

            assessmentText =
                "The model classified this location as Extreme drought severity.";

            break;


        default:

            assessmentText =
                "The model produced a drought severity classification.";

    }


    const html =

        "<div class='assessment-grid'>" +

        "<div class='assessment-item'>" +

        "<strong>NDVI Change</strong>" +

        "<span>" +

        (
            Number.isFinite(ndviChange)
                ? formatSigned(
                    ndviChange,
                    4
                )
                : "N/A"
        ) +

        "</span>" +

        "</div>" +


        "<div class='assessment-item'>" +

        "<strong>NDVI Status</strong>" +

        "<span>" +

        ndviStatus +

        "</span>" +

        "</div>" +


        "<div class='assessment-item'>" +

        "<strong>Vegetation</strong>" +

        "<span>" +

        (
            Number.isFinite(vegetation)
                ? vegetation.toFixed(2) + "%"
                : "N/A"
        ) +

        "</span>" +

        "</div>" +


        "<div class='assessment-item'>" +

        "<strong>Water Percentage</strong>" +

        "<span>" +

        (
            Number.isFinite(water)
                ? water.toFixed(4)
                : "N/A"
        ) +

        "</span>" +

        "</div>" +


        "<div class='assessment-item'>" +

        "<strong>Cloudiness</strong>" +

        "<span>" +

        (
            Number.isFinite(cloudiness)
                ? cloudiness.toFixed(4)
                : "N/A"
        ) +

        "</span>" +

        "</div>" +

        "</div>" +


        "<div class='assessment-explanation'>" +

        "<strong>Assessment:</strong><br>" +

        assessmentText +

        "</div>";


    container.innerHTML =
        html;

}


// ============================================================
// VERSION 2
// ANALYZE ANY LOCATION + IMAGE UPLOAD
// ============================================================

function setupVersion2() {

    const locationButton =
        document.getElementById(
            "analyzeLocationBtn"
        );


    const imageButton =
        document.getElementById(
            "analyzeImageBtn"
        );


    if (locationButton) {

        locationButton.addEventListener(
            "click",
            analyzeNewLocation
        );

    }


    if (imageButton) {

        imageButton.addEventListener(
            "click",
            analyzeUploadedImage
        );

    }

}


// ============================================================
// VERSION 2 — LIVE SATELLITE LOCATION ANALYSIS
// ============================================================

async function analyzeNewLocation() {

    const latitudeInput =
        document.getElementById("newLatitude");

    const longitudeInput =
        document.getElementById("newLongitude");

    const result =
        document.getElementById("newLocationPrediction");

    if (!latitudeInput || !longitudeInput) {
        return;
    }

    const latitude = Number(latitudeInput.value);
    const longitude = Number(longitudeInput.value);

    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {
        if (result) {
            result.innerHTML =
                "❌ Please enter valid latitude and longitude.";
        }
        return;
    }

    if (latitude < -90 || latitude > 90) {
        if (result) {
            result.innerHTML =
                "❌ Latitude must be between -90 and 90.";
        }
        return;
    }

    if (longitude < -180 || longitude > 180) {
        if (result) {
            result.innerHTML =
                "❌ Longitude must be between -180 and 180.";
        }
        return;
    }

    if (result) {
        result.innerHTML =
            "<div class='prediction-result'>" +
            "<h3>🛰️ Live Satellite Analysis</h3>" +
            "<p>⏳ Fetching Sentinel-2 imagery...</p>" +
            "<p>🔬 Running drought severity model...</p>" +
            "</div>";
    }

    try {

        const response = await fetch(
            "/analyze-location",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude
                })
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error ||
                "Location analysis failed."
            );
        }

        const severity =
            data.predicted_severity ||
            data.prediction ||
            "Unknown";

        const confidence =
            Number(data.confidence);

        const ndvi =
            data.ndvi || {};

        const probabilities =
            data.probabilities || {};

        const trueColorFilename =
            data.files?.true_color?.filename;

        let trueColorHTML = "";

        if (trueColorFilename) {

            const trueColorURL =
                "/live-satellite/true-color/" +
                encodeURIComponent(
                    trueColorFilename
                );

            trueColorHTML =
                "<div style='margin-top:25px;'>" +

                "<h3>🛰️ Live Sentinel-2 Imagery</h3>" +

                "<img " +
                "src='" +
                trueColorURL +
                "' " +
                "alt='Live Sentinel-2 satellite imagery' " +
                "style='width:100%;max-width:900px;" +
                "height:auto;border-radius:14px;" +
                "display:block;margin:15px auto;" +
                "box-shadow:0 8px 25px rgba(0,0,0,0.18);'" +
                "/>" +

                "</div>";
        }

        let probabilityHTML = "";

        if (
            probabilities &&
            typeof probabilities === "object"
        ) {

            probabilityHTML =
                "<div class='assessment-explanation'>" +

                "<h3>📊 Model Probability</h3>" +

                "<div style='margin-top:15px;'>";

            Object.entries(
                probabilities
            ).forEach(
                function ([className, probability]) {

                    const value =
                        Number(probability);

                    probabilityHTML +=

                        "<div style='margin-bottom:14px;'>" +

                        "<div style='display:flex;" +
                        "justify-content:space-between;" +
                        "margin-bottom:5px;'>" +

                        "<span><strong>" +
                        className +
                        "</strong></span>" +

                        "<span><strong>" +
                        value.toFixed(2) +
                        "%</strong></span>" +

                        "</div>" +

                        "<div style='width:100%;" +
                        "height:10px;" +
                        "background:#e5e7eb;" +
                        "border-radius:10px;" +
                        "overflow:hidden;'>" +

                        "<div style='width:" +
                        Math.max(
                            0,
                            Math.min(100, value)
                        ) +
                        "%;" +
                        "height:100%;" +
                        "background:linear-gradient(90deg,#2563eb,#16a34a);" +
                        "border-radius:10px;'>" +

                        "</div>" +

                        "</div>" +

                        "</div>";
                }
            );

            probabilityHTML +=
                "</div>" +
                "</div>";
        }

        if (result) {

            result.innerHTML =

                "<div class='prediction-result'>" +

                "<h2>🛰️ Live Drought Assessment</h2>" +

                "<div class='assessment-explanation'>" +

                "<strong>📍 Requested Location</strong><br>" +

                "Latitude: " +
                latitude.toFixed(6) +

                "<br>" +

                "Longitude: " +
                longitude.toFixed(6) +

                "<br><br>" +

                "<strong>Satellite:</strong> " +
                (
                    data.satellite?.source ||
                    "Sentinel-2 L2A"
                ) +

                "<br>" +

                "<strong>Index:</strong> NDVI" +

                "<br>" +

                "<strong>Date Range:</strong> " +

                (
                    data.date_range?.start ||
                    "—"
                ) +

                " to " +

                (
                    data.date_range?.end ||
                    "—"
                ) +

                "</div>" +

                "<div style='text-align:center;" +
                "margin:25px 0;'>" +

                "<h4>🌾 FINAL DROUGHT SEVERITY</h4>" +

                "<h1 class='severity-" +

                String(
                    severity
                ).toLowerCase() +

                "'>" +

                severity +

                "</h1>" +

                (
                    Number.isFinite(confidence)
                        ?
                        "<p><strong>Model Confidence:</strong> " +
                        confidence.toFixed(2) +
                        "%</p>"
                        :
                        ""
                ) +

                "</div>" +

                probabilityHTML +

                "<div class='assessment-grid'>" +

                "<div class='assessment-item'>" +
                "<strong>Mean NDVI</strong>" +
                "<span>" +
                Number(ndvi.mean).toFixed(4) +
                "</span>" +
                "</div>" +

                "<div class='assessment-item'>" +
                "<strong>Median NDVI</strong>" +
                "<span>" +
                Number(ndvi.median).toFixed(4) +
                "</span>" +
                "</div>" +

                "<div class='assessment-item'>" +
                "<strong>Minimum NDVI</strong>" +
                "<span>" +
                Number(ndvi.minimum).toFixed(4) +
                "</span>" +
                "</div>" +

                "<div class='assessment-item'>" +
                "<strong>Maximum NDVI</strong>" +
                "<span>" +
                Number(ndvi.maximum).toFixed(4) +
                "</span>" +
                "</div>" +

                "<div class='assessment-item'>" +
                "<strong>NDVI Std. Deviation</strong>" +
                "<span>" +
                Number(
                    ndvi.standard_deviation
                ).toFixed(4) +
                "</span>" +
                "</div>" +

                "<div class='assessment-item'>" +
                "<strong>Valid Pixels</strong>" +
                "<span>" +
                Number(
                    ndvi.valid_pixels
                ).toLocaleString() +
                "</span>" +
                "</div>" +

                "</div>" +

                trueColorHTML +

                "<div class='assessment-explanation'>" +

                "<h3>🔬 Model Assessment</h3>" +

                "<p>" +

                "The requested coordinates were analyzed " +
                "using live Sentinel-2 satellite imagery " +
                "and the trained drought severity model." +

                "</p>" +

                "<p>" +

                "<strong>Final classification:</strong> " +
                severity +

                "</p>" +

                "</div>" +

                "</div>";
        }

        if (
            typeof map !== "undefined" &&
            map
        ) {

            map.flyTo(
                [
                    latitude,
                    longitude
                ],
                14,
                {
                    animate: true,
                    duration: 1.5
                }
            );

            if (
                window.requestedLocationMarker
            ) {

                map.removeLayer(
                    window.requestedLocationMarker
                );
            }

            window.requestedLocationMarker =
                L.marker(
                    [
                        latitude,
                        longitude
                    ]
                ).addTo(map);

            window.requestedLocationMarker
                .bindPopup(
                    "<strong>📍 Live Drought Analysis</strong><br>" +
                    "Latitude: " +
                    latitude.toFixed(6) +
                    "<br>" +
                    "Longitude: " +
                    longitude.toFixed(6) +
                    "<br><br>" +
                    "<strong>Severity: " +
                    severity +
                    "</strong>"
                )
                .openPopup();
        }

    }
    catch (error) {

        console.error(
            "Live location analysis error:",
            error
        );

        if (result) {

            result.innerHTML =
                "<div class='prediction-result'>" +
                "❌ " +
                error.message +
                "</div>";
        }
    }
}


// ============================================================
// VERSION 2 — IMAGE UPLOAD
// ============================================================

async function analyzeUploadedImage() {

    const input =
        document.getElementById(
            "satelliteUpload"
        );

    const result =
        document.getElementById(
            "newLocationPrediction"
        );


    // ========================================================
    // CHECK FILE
    // ========================================================

    if (!input || !input.files.length) {

        if (result) {

            result.innerHTML =
                "❌ Please select a satellite image first.";

        }

        return;
    }


    const file =
        input.files[0];


    // ========================================================
    // CHECK FILE TYPE
    // ========================================================

    const allowedExtensions = [

        ".tif",
        ".tiff",
        ".png",
        ".jpg",
        ".jpeg"

    ];


    const filename =
        file.name.toLowerCase();


    const supported =
        allowedExtensions.some(
            extension =>
                filename.endsWith(
                    extension
                )
        );


    if (!supported) {

        if (result) {

            result.innerHTML =
                "❌ Unsupported file format.";

        }

        return;
    }


    // ========================================================
    // SHOW LOADING
    // ========================================================

    if (result) {

        result.innerHTML =
            "⏳ Uploading and analyzing satellite image...";

    }


    // ========================================================
    // CREATE FORM DATA
    // ========================================================

    const formData =
        new FormData();


    formData.append(
        "image",
        file
    );


    try {

        // ====================================================
        // SEND IMAGE TO FLASK
        // ====================================================

        const response =
            await fetch(
                "/analyze-image",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        // ====================================================
        // CHECK SERVER RESPONSE
        // ====================================================

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Image analysis failed."
            );

        }


        if (!data.success) {

            throw new Error(
                data.error ||
                "Image analysis failed."
            );

        }


        // ====================================================
        // GET IMAGE FEATURES
        // ====================================================

        const stats =
            data.image_features || {};


        const mean =
            Number(
                stats.mean
            );


        const standardDeviation =
            Number(
                stats.standard_deviation
            );


        const minimum =
            Number(
                stats.minimum
            );


        const maximum =
            Number(
                stats.maximum
            );


        const median =
            Number(
                stats.median
            );


        // ====================================================
        // GET PREDICTION
        // ====================================================

        const severity =
            data.predicted_severity ||
            data.prediction ||
            "Unknown";


        const confidence =
            data.confidence;




        // ====================================================
        // DROUGHT EXPLANATION & RECOMMENDATION
        // ====================================================

        let severityTitle = "";
        let severityExplanation = "";
        let severityRecommendation = "";

        switch (
        String(severity).toLowerCase()
        ) {

            case "low":

                severityTitle =
                    "🟢 Low Drought";

                severityExplanation =
                    "The area currently shows relatively low drought stress based on the uploaded satellite image.";

                severityRecommendation =
                    "Continue routine monitoring of vegetation and water conditions.";

                break;


            case "moderate":

                severityTitle =
                    "🟠 Moderate Drought";

                severityExplanation =
                    "The area shows noticeable drought stress and should be monitored more closely.";

                severityRecommendation =
                    "Continue monitoring vegetation and water conditions and consider water-conservation measures.";

                break;


            case "severe":

                severityTitle =
                    "⚠️ Severe Drought";

                severityExplanation =
                    "The area shows significant drought stress based on the satellite-image analysis.";

                severityRecommendation =
                    "Increase monitoring and consider appropriate water-conservation and agricultural management measures.";

                break;


            case "extreme":

                severityTitle =
                    "🚨 Extreme Drought";

                severityExplanation =
                    "The area indicates very high drought stress and may require immediate attention.";

                severityRecommendation =
                    "Prioritize water-resource management and closely monitor vegetation and agricultural conditions.";

                break;


            default:

                severityTitle =
                    "🌾 Drought Assessment";

                severityExplanation =
                    "The uploaded satellite image has been analyzed by the machine-learning model.";

                severityRecommendation =
                    "Continue monitoring the area and review additional environmental information.";

                break;
        }

        // ====================================================
        // CONFIDENCE TEXT
        // ====================================================

        let confidenceHTML = "";


        if (
            confidence !== null &&
            confidence !== undefined &&
            Number.isFinite(
                Number(confidence)
            )
        ) {

            confidenceHTML =

                "<div class='assessment-item'>" +

                "<strong>Model Confidence</strong>" +

                "<span>" +

                Number(
                    confidence
                ).toFixed(2) +

                "%" +

                "</span>" +

                "</div>";

        }


        // ====================================================
        // PROBABILITY DETAILS
        // ====================================================

        let probabilityHTML = "";


        if (
            data.probabilities &&
            typeof data.probabilities === "object"
        ) {

            probabilityHTML =

                "<div class='assessment-explanation'>" +

                "<strong>Prediction Probabilities</strong>" +

                "<div style='margin-top:10px;'>";


            Object.entries(
                data.probabilities
            ).forEach(
                function ([className, probability]) {

                    probabilityHTML +=

                        "<div style='display:flex; justify-content:space-between; margin:6px 0;'>" +

                        "<span>" +

                        className +

                        "</span>" +

                        "<strong>" +

                        Number(
                            probability
                        ).toFixed(2) +

                        "%</strong>" +

                        "</div>";

                }
            );


            probabilityHTML +=

                "</div>" +

                "</div>";

        }





        // ====================================================
        // DISPLAY COMPLETE RESULT
        // ====================================================

        const previewURL =
            URL.createObjectURL(file);

        if (result) {

            result.innerHTML =

                "<div class='prediction-result'>" +

                "<h3>🛰️ Satellite Image Analysis</h3>" +


                "<p>" +
                "<strong>File:</strong> " +
                data.filename +
                "</p>" +

                "<div class='uploaded-image-preview'>" +
                "<h4>Uploaded Satellite Image</h4>" +
                "<img " +
                "src='" + previewURL + "' " +
                "alt='Uploaded Satellite Image'>" +
                "</div>" +


                // --------------------------------------------
                // PREDICTION
                // --------------------------------------------

                "<div style='text-align:center; margin:20px 0;'>" +

                "<h4>🌾 Predicted Drought Severity</h4>" +

                "<h1 class='severity-" +

                String(
                    severity
                ).toLowerCase() +

                "'>" +

                severity +

                "</h1>" +

                "</div>" +


                // --------------------------------------------
                // IMAGE FEATURES
                // --------------------------------------------

                "<div class='assessment-grid'>" +


                "<div class='assessment-item'>" +

                "<strong>Mean Value</strong>" +

                "<span>" +

                (
                    Number.isFinite(mean)
                        ? mean.toFixed(4)
                        : "N/A"
                ) +

                "</span>" +

                "</div>" +


                "<div class='assessment-item'>" +

                "<strong>Standard Deviation</strong>" +

                "<span>" +

                (
                    Number.isFinite(
                        standardDeviation
                    )
                        ? standardDeviation.toFixed(4)
                        : "N/A"
                ) +

                "</span>" +

                "</div>" +


                "<div class='assessment-item'>" +

                "<strong>Minimum</strong>" +

                "<span>" +

                (
                    Number.isFinite(minimum)
                        ? minimum.toFixed(4)
                        : "N/A"
                ) +

                "</span>" +

                "</div>" +


                "<div class='assessment-item'>" +

                "<strong>Maximum</strong>" +

                "<span>" +

                (
                    Number.isFinite(maximum)
                        ? maximum.toFixed(4)
                        : "N/A"
                ) +

                "</span>" +

                "</div>" +


                "<div class='assessment-item'>" +

                "<strong>Median</strong>" +

                "<span>" +

                (
                    Number.isFinite(median)
                        ? median.toFixed(4)
                        : "N/A"
                ) +

                "</span>" +

                "</div>" +


                confidenceHTML +


                "</div>" +


                // --------------------------------------------
                // PROBABILITIES
                // --------------------------------------------

                probabilityHTML +


                // --------------------------------------------
                // DROUGHT INTERPRETATION
                // --------------------------------------------

                "<div class='assessment-explanation' style='margin-top:20px;'>" +

                "<h3>" +

                severityTitle +

                "</h3>" +

                "<p>" +

                severityExplanation +

                "</p>" +

                "<p>" +

                "<strong>Recommended Action:</strong><br>" +

                severityRecommendation +

                "</p>" +

                "</div>" +


                "<div class='assessment-explanation'>" +

                "✅ Satellite image processed successfully." +

                "<br><br>" +

                "The trained image-based machine learning model analyzed the uploaded image and generated the drought severity classification." +

                "</div>" +


                "</div>";

        }


    }

    catch (error) {

        console.error(
            "Image upload error:",
            error
        );


        if (result) {

            result.innerHTML =
                "❌ " +
                error.message;

        }

    }

}

// ============================================================
// ANALYTICS
// ============================================================

async function loadAnalytics() {

    try {

        const response =
            await fetch(
                "/analytics"
            );


        if (!response.ok) {

            throw new Error(
                "Analytics server returned " +
                response.status
            );

        }


        const data =
            await response.json();


        if (data.severity_distribution) {

            createSeverityChart(
                data.severity_distribution
            );

        }


        if (data.ndvi_by_severity) {

            createNDVIChart(
                data.ndvi_by_severity
            );

        }


        if (data.vegetation_by_severity) {

            createVegetationChart(
                data.vegetation_by_severity
            );

        }


        if (data.year_severity) {

            createYearlySeverityChart(
                data.year_severity
            );

        }

    }
    catch (error) {

        console.error(
            "Analytics error:",
            error
        );

    }

}


// ============================================================
// SEVERITY CHART
// ============================================================

function createSeverityChart(data) {

    const canvas =
        document.getElementById(
            "severityChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (severityChartInstance) {

        severityChartInstance.destroy();

    }


    const labels =
        data.map(
            item => item.severity
        );


    const values =
        data.map(
            item => item.count
        );


    severityChartInstance =
        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            data: values
                        }
                    ]

                },

                options: {

                    responsive: true,

                    plugins: {

                        legend: {
                            position: "bottom"
                        }

                    }

                }

            }
        );

}


// ============================================================
// NDVI CHART
// ============================================================

function createNDVIChart(data) {

    const canvas =
        document.getElementById(
            "ndviChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (ndviChartInstance) {

        ndviChartInstance.destroy();

    }


    const labels =
        data.map(
            item => item.severity
        );


    const values =
        data.map(
            item => item.value
        );


    ndviChartInstance =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            label:
                                "Average NDVI",

                            data: values
                        }
                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {
                            beginAtZero: true,

                            title: {
                                display: true,
                                text: "NDVI"
                            }

                        }

                    }

                }

            }
        );

}


// ============================================================
// VEGETATION CHART
// ============================================================

function createVegetationChart(data) {

    const canvas =
        document.getElementById(
            "vegetationChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (vegetationChartInstance) {

        vegetationChartInstance.destroy();

    }


    const labels =
        data.map(
            item => item.severity
        );


    const values =
        data.map(
            item => item.value
        );


    vegetationChartInstance =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            label:
                                "Average Vegetation %",

                            data: values
                        }
                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true,

                            title: {

                                display: true,

                                text:
                                    "Vegetation %"

                            }

                        }

                    }

                }

            }
        );

}


// ============================================================
// YEARLY SEVERITY CHART
// ============================================================

function createYearlySeverityChart(data) {

    const canvas =
        document.getElementById(
            "yearSeverityChart"
        );


    if (
        !canvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }


    if (yearlySeverityChartInstance) {

        yearlySeverityChartInstance.destroy();

    }


    const years = [
        ...new Set(
            data.map(
                item => item.year
            )
        )
    ].sort();


    const severityNames = [
        "Low",
        "Moderate",
        "Severe",
        "Extreme"
    ];


    const datasets =
        severityNames.map(
            function (severity) {

                return {

                    label:
                        severity,

                    data:
                        years.map(
                            function (year) {

                                const found =
                                    data.find(
                                        item =>
                                            Number(
                                                item.year
                                            ) ===
                                            Number(
                                                year
                                            )
                                            &&
                                            item.severity ===
                                            severity
                                    );

                                return found
                                    ? found.count
                                    : 0;

                            }
                        ),

                    tension: 0.3

                };

            }
        );


    yearlySeverityChartInstance =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels: years,

                    datasets: datasets

                },

                options: {

                    responsive: true,

                    interaction: {

                        mode: "index",

                        intersect: false

                    },

                    scales: {

                        x: {

                            title: {

                                display: true,

                                text: "Year"

                            }

                        },

                        y: {

                            beginAtZero: true,

                            title: {

                                display: true,

                                text:
                                    "Number of Locations"

                            }

                        }

                    }

                }

            }
        );

}


// ============================================================
// HELPER — SET TEXT
// ============================================================

function setText(id, value) {

    const element =
        document.getElementById(id);


    if (element) {

        element.innerText =
            value ?? "—";

    }

}


// ============================================================
// HELPER — SET HTML
// ============================================================

function setHTML(id, value) {

    const element =
        document.getElementById(id);


    if (element) {

        element.innerHTML =
            value;

    }

}


// ============================================================
// HELPER — FORMATTED NUMBER
// ============================================================

function setFormattedText(
    id,
    value,
    decimals,
    suffix = ""
) {

    const element =
        document.getElementById(id);


    if (!element) {
        return;
    }


    const number =
        Number(value);


    if (
        Number.isFinite(number)
    ) {

        element.innerText =
            number.toFixed(
                decimals
            ) +
            suffix;

    }
    else {

        element.innerText =
            value ?? "—";

    }

}


// ============================================================
// HELPER — SIGNED NUMBER
// ============================================================

function formatSigned(
    value,
    decimals
) {

    const number =
        Number(value);


    if (
        !Number.isFinite(number)
    ) {

        return "N/A";

    }


    if (number > 0) {

        return (
            "+" +
            number.toFixed(
                decimals
            )
        );

    }


    return number.toFixed(
        decimals
    );
}
