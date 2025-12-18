# 🌧️ Flood Alert System (ML‑Powered + SMS Alerts)

An end‑to‑end **machine‑learning–driven flood risk prediction and alert system**.
The system ingests historical weather data, learns flood‑risk patterns, estimates **probabilistic flood risk**, and delivers **real‑time alerts via SMS** using Twilio.

This project is designed as a **proof‑of‑concept** showing how data science, environmental reasoning, and real‑world alerting can be combined into a deployable system.

---

## 🚀 Key Features

* **Machine Learning–based flood risk prediction** (Random Forest)
* **Probabilistic risk output** (not just binary yes/no)
* **Real‑time user input support** via web interface
* **Automated SMS alerts** using Twilio
* **Physically‑motivated features** (rainfall accumulation, humidity, drainage, elevation)
* **Scalable backend design** (ready for telecom / government integration)

---

## 🧠 Core Idea

Flooding is not caused by a single factor.

This system models flooding as a balance between:

**Water Load**

* Rainfall in the last 24 hours
* Rainfall accumulation over 72 hours
* Relative humidity (soil/air saturation)

**Environmental Capacity**

* Drainage efficiency
* Elevation (flood‑prone lowlands vs higher ground)

The ML model learns **how combinations of these factors interact**, instead of relying on rigid if‑else rules.

---

## 📊 Data Source

* **Weather data:** Retrieved using the `meteostat` API
* **Location:** Lagos, Nigeria
* **Time range:** 2015 → Present

Since real drainage and elevation datasets are not publicly available at high resolution, **synthetic but realistic demo scores** are generated:

* `drainage_score ∈ [0,1]`
* `elevation_score ∈ [0,1]`

> ⚠️ These are placeholders for demonstration purposes and can be replaced with real GIS / urban planning data in future versions.

---

## 🏗️ Project Structure

```text
├── app.py                # Flask backend + Twilio SMS integration           
├── data/
│   ├──  data.py          # Weather data collection & preprocessing
│   └── Lagos CSV         # Generated dataset
├── Model/
│   ├── flood_model.pkl  # Trained model + scaler
│   └──predict.py         # Model training, evaluation, and serialization
├── templates/
│   └── index.html        # Frontend UI
├── static/
│   ├── css/style.css
│   └── js/script.js
├── .env                  # Environment variables (Twilio credentials)
├── .README.md                 
└── requirements.txt
```

---

## ⚙️ How the System Works

### 1️⃣ Data Collection (`data.py`)

* Fetches **hourly precipitation and humidity data** from Meteostat
* Adds demo `drainage_score` and `elevation_score`
* Saves cleaned data to CSV

### 2️⃣ Feature Engineering (`predict.py`)

* Aggregates hourly data into **daily summaries**
* Computes:

  * Rainfall in last 24 hours
  * Rainfall accumulation over 72 hours
* Defines flood labels using **physically reasonable conditions**

### 3️⃣ Model Training

* **RandomForestClassifier** used for robustness to nonlinear relationships
* Class imbalance handled via **oversampling + shuffling**
* Features scaled using **StandardScaler** (fit on training set only)

### 4️⃣ Risk Prediction

The model outputs a **probability**:

```text
Risk Probability ∈ [0,1]
```

Mapped to human‑readable alerts:

| Probability | Alert Level                |
| ----------- | -------------------------- |
| ≥ 0.80      | HIGH RISK – Evacuate       |
| 0.40 – 0.79 | MODERATE RISK – Stay Alert |
| < 0.40      | LOW RISK                   |

### 5️⃣ Deployment (`app.py`)

* Flask API receives user inputs
* Model predicts flood probability
* Alert message returned to UI
* **Optional SMS sent instantly** via Twilio

---

## 📩 SMS Alert System (Important)

⚠️ **Current Limitation**

For SMS alerts to be successfully delivered:

* The **recipient phone number must be a verified Twilio number**
* Or the sender must be operating under a **Twilio trial/paid account**

This is a **Twilio restriction**, not a system limitation.

🔮 **Future Plan**

* Integration with local telecom providers
* Government emergency broadcast systems
* WhatsApp / USSD alerts

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone_number
```

---

## ▶️ Running the Project

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Generate Dataset

```bash
python data.py
```

### 3️⃣ Train Model

```bash
python predict.py
```

### 4️⃣ Run Flask App

```bash
python app.py
```

Visit:

```text
http://localhost:10000
```

---

## 🧪 Example Test Input

```json
{
  "rain_24h": 15,
  "rain_72h": 70,
  "rhum": 70,
  "drainage_score": 0.5,
  "elevation_score": 0.2,
  "phone_numbers": "+2348012345678"
}
```

---

## 🎯 Why This Project Matters

* Demonstrates **applied machine learning**, not toy classification
* Shows **probabilistic decision‑making** under uncertainty
* Bridges **data science → real‑world impact**
* Easily extensible to:

  * Other cities
  * Real GIS datasets
  * National early‑warning systems

---

## 🛠️ Future Improvements

* Replace synthetic scores with real GIS / urban data
* Time‑aware models (LSTM / Temporal CNN)
* Spatial flood maps & heatmaps
* Telecom‑level SMS broadcasting
* Model retraining with live data streams

---

## 👤 Author

Built with focus, urgency, and engineering discipline by **Meeks**.

> *This project was intentionally designed to balance speed, realism, and explainability under tight time constraints.*

---

🔥 **If you understand this README, you understand the system.**
