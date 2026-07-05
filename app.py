from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)

with open('Model/flood_model.pkl', 'rb') as f:
    model, scaler = pickle.load(f)

features = ['rain_24h', 'rain_72h', 'rhum', 'drainage_score', 'elevation_score']

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
    """IoT ingestion endpoint — accepts sensor readings and returns flood risk."""
    data = request.json

    # Extract phone numbers if provided
    phone_numbers = data.pop('phone_numbers', '')
    
    sample = pd.DataFrame([data])[features]
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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
