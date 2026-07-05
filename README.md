# IoT-Ready Flood Risk Prediction Prototype

An **ML-powered flood risk prediction system** designed as a prototype to demonstrate how IoT sensor data can be received and used for real-time flood risk assessment.

The system exposes a simple API endpoint that accepts sensor readings — whether from a web form or directly from IoT devices (rain gauges, humidity sensors, drainage monitors, elevation sensors) — runs them through a trained Random Forest model, and returns a probabilistic risk score with optional SMS alerts.

---

## IoT Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     IoT Sensors                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Rain     │  │ Humidity │  │ Drainage │  │ Elevation │  │
│  │ Gauge    │  │ Sensor   │  │ Monitor  │  │ (GPS)     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │             │             │              │        │
└───────┼─────────────┼─────────────┼──────────────┼────────┘
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                        │
                        ▼  HTTP POST /predict (JSON)
              ┌─────────────────────────┐
              │     Flask API (app.py)   │
              │  ┌───────────────────┐  │
              │  │  StandardScaler   │  │
              │  └────────┬──────────┘  │
              │           ▼             │
              │  ┌───────────────────┐  │
              │  │ Random Forest     │  │
              │  │ Model (pickle)    │  │
              │  └────────┬──────────┘  │
              └───────────┼─────────────┘
                          ▼
              ┌──────────────────────┐
              │   Risk Probability    │
              │    (0% – 100%)       │
              └──────────┬───────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌────────────────┐      ┌──────────────────┐
    │  Web Dashboard │      │  SMS Alert       │
    │  (color-coded) │      │  (via Twilio)    │
    └────────────────┘      └──────────────────┘
```

The `/predict` endpoint accepts JSON with five sensor readings and an optional phone number. This is the same endpoint IoT devices would call — making the system ready for hardware integration with no backend changes.

---

## Key Features

- **ML-based flood risk prediction** (Random Forest, 99.2% accuracy)
- **Probabilistic output** — not just binary yes/no
- **IoT-ready API** — any device can POST sensor data to `/predict`
- **Web dashboard** for manual input and visualization
- **Optional SMS alerts** via Twilio
- **Physically-motivated features** (rainfall accumulation, humidity, drainage, elevation)

---

## Core Idea

Flooding is not caused by a single factor. This system models flooding as a balance between:

**Water Load**
- Rainfall in the last 24 hours
- Rainfall accumulation over 72 hours
- Relative humidity (soil/air saturation)

**Environmental Capacity**
- Drainage efficiency
- Elevation (flood-prone lowlands vs higher ground)

The ML model learns how combinations of these factors interact, instead of relying on rigid if-else rules.

---

## Data Source

- **Weather data:** Retrieved using the `meteostat` API
- **Location:** Lagos, Nigeria
- **Time range:** 2015 → Present

In a full deployment, `drainage_score` and `elevation_score` would come from real IoT sensors. For this prototype, **synthetic but realistic demo scores** are generated:

- `drainage_score ∈ [0,1]` — placeholders for real drainage sensor data
- `elevation_score ∈ [0,1]` — placeholder for real GPS/elevation data

> These are placeholders demonstrating that the system **can receive and act on** these values. Swap in real IoT sensor readings in production.

---

## Project Structure

```text
├── app.py                 # Flask API — the IoT ingestion endpoint
├── Model/
│   ├── predict.py         # Model training, evaluation, serialization
│   └── flood_model.pkl    # Trained (model, scaler) pair
├── data/
│   ├── data.py            # Weather data collection from Meteostat
│   └── Lagos CSV          # Generated historical dataset
├── templates/
│   └── index.html         # Web UI for manual input
├── static/
│   ├── css/style.css
│   └── js/script.js
├── .env                   # Twilio credentials (optional)
├── requirements.txt
└── README.md
```

---

## How the System Works

### 1. Data Collection (`data/data.py`)
- Fetches hourly precipitation and humidity from Meteostat
- Generates synthetic drainage/elevation scores (IoT data placeholders)
- Saves cleaned dataset to CSV

### 2. Model Training (`Model/predict.py`)
- Aggregates hourly data into daily summaries
- Engineers features: `rain_24h`, `rain_72h`
- Labels flood events using physically reasonable conditions
- Trains a **Random Forest** (200 trees, optimised depth)
- Evaluates with accuracy, precision, recall, F1, ROC-AUC, cross-validation
- Prints feature importances
- Saves trained model + scaler to `flood_model.pkl`

### 3. Risk Prediction

The model outputs a probability (0%–100%) mapped to alert levels:

| Probability  | Alert Level                |
| ------------ | -------------------------- |
| ≥ 80%        | HIGH RISK – Evacuate       |
| 40% – 79%    | MODERATE RISK – Stay Alert |
| < 40%        | LOW RISK                   |

### 4. Deployment (`app.py`)
- Flask server on `0.0.0.0:10000`
- **`POST /predict`** — accepts JSON with sensor readings, returns risk alert
- **`GET /`** — serves the web dashboard
- Optional SMS sent via Twilio (gracefully disabled if credentials missing)

---

## IoT Integration

The system is designed so that IoT hardware can replace the web form entirely:

1. **Rain gauge** → `rain_24h`, `rain_72h`
2. **Humidity sensor** → `rhum`
3. **Drainage sensor** → `drainage_score`
4. **GPS / altimeter** → `elevation_score`

Each sensor posts its readings to the same `/predict` endpoint. The model processes them identically whether submitted from a browser or an ESP32/Arduino.

### Example IoT Payload

```json
{
  "rain_24h": 15.0,
  "rain_72h": 70.0,
  "rhum": 70.0,
  "drainage_score": 0.5,
  "elevation_score": 0.2,
  "phone_numbers": "+2348012345678"
}
```

---

## SMS Alert System

SMS delivery requires a Twilio account. If credentials are missing from `.env`, the app runs normally and simply skips SMS — the web dashboard still works.

### Environment Variables

Create a `.env` file in the root directory:

```env
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone_number
```

---

## Running the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Dataset
```bash
python data/data.py
```

### 3. Train Model
```bash
python Model/predict.py
```

### 4. Run Flask App
```bash
python app.py
```

Visit `https://team-safe-haven-floodalertapp-e7sm.vercel.app/`

---

## Future Improvements

- Replace synthetic scores with real IoT sensor hardware
- Time-aware models (LSTM / Temporal CNN)
- Spatial flood maps & heatmaps
- Telecom-level SMS broadcasting
- Model retraining with live IoT data streams

---

## Author

Built with focus, urgency, and engineering discipline by **Meeks**.

> This prototype was designed to prove that IoT sensor data can be ingested and used for real-time ML-driven flood risk prediction — a foundation for a full-scale early warning system.
