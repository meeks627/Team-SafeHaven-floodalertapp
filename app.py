from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import sys
import pickle
import pandas as pd
import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from data.ingest import insert_reading, get_reading_count
from Model.predict import load_model, FEATURES, MODEL_PATH

load_dotenv()
app = Flask(__name__)

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

client = None
if TWILIO_SID and TWILIO_AUTH and TWILIO_PHONE:
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH)
        print("Twilio client initialized")
    except Exception as e:
        print(f"Twilio init failed (SMS disabled): {e}")
else:
    print("Twilio credentials missing (SMS disabled)")

_current_model = None
_current_scaler = None
_model_mtime = 0


def get_model():
    global _current_model, _current_scaler, _model_mtime
    mtime = os.path.getmtime(MODEL_PATH)
    if mtime != _model_mtime:
        _current_model, _current_scaler = load_model(MODEL_PATH)
        _model_mtime = mtime
        print("Model reloaded from disk")
    return _current_model, _current_scaler


def alert_message(risk_prob):
    if risk_prob >= 0.8:
        alert = "HIGH RISK: Flood likely in next 6 hours. Evacuate."
    elif risk_prob >= 0.4:
        alert = "MODERATE RISK: Be on alert."
    else:
        alert = "LOW RISK"
    return f'Risk Probability: {risk_prob:.2%}\n{alert}'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Return flood risk for given sensor readings."""
    data = request.json

    phone_numbers = data.pop('phone_numbers', '')

    model, scaler = get_model()

    sample = pd.DataFrame([data])[FEATURES]
    sample_scaled = scaler.transform(sample.values)

    risk_prob = model.predict_proba(sample_scaled)[0, 1]
    alert = alert_message(risk_prob)

    if phone_numbers and client:
        numbers = [num.strip() for num in phone_numbers.split(',')]
        try:
            for num in numbers:
                client.messages.create(
                    body=alert,
                    from_=TWILIO_PHONE,
                    to=num
                )
            print("SMS sent successfully")
        except Exception as e:
            print(f"SMS failed: {e}")
    elif phone_numbers and not client:
        print("SMS skipped: Twilio not configured")

    return jsonify({'alert': alert})


@app.route('/ingest', methods=['POST'])
def ingest():
    """Accept IoT sensor readings and store in database."""
    required = ['rain_24h', 'rain_72h', 'rhum', 'drainage_score', 'elevation_score']
    data = request.json

    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({'status': 'error', 'missing': missing}), 400

    try:
        row_id = insert_reading(data)
        count = get_reading_count()
        return jsonify({'status': 'ok', 'id': row_id, 'total_readings': count})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check — shows DB record count."""
    return jsonify({
        'status': 'ok',
        'readings_stored': get_reading_count(),
        'model_loaded': _current_model is not None
    })


if __name__ == '__main__':
    _current_model, _current_scaler = load_model(MODEL_PATH)
    _model_mtime = os.path.getmtime(MODEL_PATH)
    app.run(host="0.0.0.0", port=10000)
