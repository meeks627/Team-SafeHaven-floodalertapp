# IoT-Ready Flood Risk Prediction Prototype

An **ML-powered flood risk prediction system** designed as a prototype to demonstrate how IoT sensor data can be received and used for real-time flood risk assessment. The model runs on **Vercel** (live URL below), while data ingestion and retraining happen **locally**.

---

## Live Deployment

The prediction API is live on Vercel:

**[https://team-safehaven-floodalertapp.vercel.app](https://team-safehaven-floodalertapp.vercel.app)**

### Available endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/predict` | POST | Send 5 sensor readings → get flood risk |
| `/health` | GET | Health check |

### Test it

```bash
curl -X POST https://team-safehaven-floodalertapp.vercel.app/predict \
  -H "Content-Type: application/json" \
  -d '{"rain_24h":15,"rain_72h":70,"rhum":70,"drainage_score":0.5,"elevation_score":0.2}'
```

---

## Architecture

```
LOCAL MACHINE                        VERCEL
─────────────                        ──────
                                       │
IoT Sensors ──POST /ingest──► SQLite   │
        │                              │
        ▼                              │
  runs retrain.py                      │
  → trains new model                   │
  → git commit + push ───────────────► auto-deploys
                                       │ serves:
                                       │  GET  /  (UI)
                                       │  POST /predict  (ML inference)
                                       │  GET  /health
```

- **Vercel** handles prediction requests (stateless, always-on)
- **Local** handles data collection (SQLite database) and model retraining
- When you retrain locally and push the new model, Vercel auto-deploys

---

## Key Features

- **ML-based flood risk prediction** (Random Forest, 99.2% accuracy)
- **Probabilistic output** — not just binary yes/no
- **Always-on API** — deployed on Vercel
- **Local data collection** — IoT sensors POST to local `/ingest` endpoint, stored in SQLite
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

`drainage_score` and `elevation_score` are synthetic placeholders for demonstration. In a full deployment, these would come from real IoT sensors.

---

## Project Structure

```text
├── app.py                 # Flask API — deployed on Vercel, also runs locally
├── vercel.json            # Vercel deployment config
├── Model/
│   ├── predict.py         # Model training functions + load_model()
│   └── flood_model.pkl    # Trained (model, scaler) pair
├── data/
│   ├── __init__.py
│   ├── data.py            # Weather data collection from Meteostat
│   ├── Lagos CSV          # Generated historical dataset
│   ├── ingest.py          # SQLite database helpers (local only)
│   ├── retrain.py         # Automated retrainer (local only)
│   └── scheduler.py       # Daily retrain timer (local only, optional)
├── templates/
│   └── index.html         # Web UI
├── static/
│   ├── css/style.css
│   └── js/script.js
├── .env                   # Twilio credentials (local only)
├── requirements.txt
└── README.md
```

---

## Local Workflow

### 1. Run locally (for data ingestion + training)

```bash
pip install -r requirements.txt

# Fetch historical weather data (one-time)
python data/data.py

# Collect IoT sensor data locally
python app.py
# Now POST sensor readings to http://localhost:10000/ingest
```

IoT sensors POST to the local `/ingest` endpoint:

```bash
curl -X POST http://localhost:10000/ingest \
  -H "Content-Type: application/json" \
  -d '{"rain_24h":12,"rain_72h":45,"rhum":82,"drainage_score":0.3,"elevation_score":0.4}'
```

### 2. Retrain the model (when you have enough new data)

```bash
python data/retrain.py
```

This merges all IoT sensor data from SQLite with the historical Meteostat data and retrains the Random Forest model.

### 3. Deploy the updated model to Vercel

```bash
git add Model/flood_model.pkl
git commit -m "Retrain model with new IoT data"
git push origin main
```

Vercel auto-deploys — the updated model goes live in seconds.

---

## How the System Works

### 1. Data Collection (`data/data.py`)
- Fetches hourly precipitation and humidity from Meteostat
- Generates synthetic drainage/elevation scores (IoT data placeholders)

### 2. IoT Ingestion (`POST /ingest`)
- IoT sensors POST readings to the local endpoint
- Stored in SQLite (`data/sensor_data.db`)

### 3. Model Training (`data/retrain.py`)
- Merges IoT data + historical data
- Engineers features: `rain_24h`, `rain_72h`
- Labels flood events using physically reasonable conditions
- Trains a **Random Forest** (200 trees)
- Evaluates with accuracy, precision, recall, F1, ROC-AUC

### 4. Risk Prediction (on Vercel)

The model outputs a probability (0%–100%) mapped to alert levels:

| Probability  | Alert Level                |
| ------------ | -------------------------- |
| ≥ 80%        | HIGH RISK – Evacuate       |
| 40% – 79%    | MODERATE RISK – Stay Alert |
| < 40%        | LOW RISK                   |

---

## SMS Alert System

SMS delivery via Twilio is optional. Set credentials in `.env` to enable:

```env
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone_number
```

On Vercel, set these as Environment Variables in the dashboard.

---

## IoT Integration

The system is designed so that IoT hardware can replace the web form entirely:

1. **Rain gauge** → `rain_24h`, `rain_72h`
2. **Humidity sensor** → `rhum`
3. **Drainage sensor** → `drainage_score`
4. **GPS / altimeter** → `elevation_score`

Each sensor posts its readings to the local `/ingest` endpoint. The model processes them identically whether submitted from a browser or an ESP32/Arduino.

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

## Future Improvements

- Replace synthetic scores with real IoT sensor hardware
- Automate retraining with GitHub Actions
- Time-aware models (LSTM / Temporal CNN)
- Spatial flood maps & heatmaps
- Telecom-level SMS broadcasting

---

## Author

Built with focus, urgency, and engineering discipline by **Meeks**.

> This prototype was designed to prove that IoT sensor data can be ingested and used for real-time ML-driven flood risk prediction — a foundation for a full-scale early warning system.
