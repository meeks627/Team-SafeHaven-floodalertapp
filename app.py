from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import pandas as pd
from twilio.rest import Client   # ✅ CHANGED
from dotenv import load_dotenv
import os


with open('Model/flood_model.pkl', 'rb') as f:
    model, scaler = pickle.load(f)

features = ['rain_24h', 'rain_72h', 'rhum', 'drainage_score', 'elevation_score']

app = Flask(__name__)
load_dotenv()

# ✅ Twilio credentials (env vars)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

client = Client(TWILIO_SID, TWILIO_AUTH)  # ✅ CHANGED


def alert_message(risk_prob):
    if risk_prob >= 0.8:
        alert = "HIGH RISK: Flood likely in next 6 hours. Evacuate."
    elif risk_prob >= 0.4:
        alert = "MODERATE RISK: Be on alert."
    else:
        alert = "LOW RISK"
    return f'Risk Probability: {risk_prob:.2f}\n{alert}'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    # Extract phone numbers if provided
    phone_numbers = data.pop('phone_numbers', '')
    
    # Prepare input for model
    sample = pd.DataFrame([data])
    sample[features] = scaler.transform(sample[features])
    
    # Predict risk probability
    risk_prob = model.predict_proba(sample)[0,1]
    alert = alert_message(risk_prob)

    # ✅ Send SMS with Twilio (logic unchanged)
    if phone_numbers:
        numbers = [num.strip() for num in phone_numbers.split(',')]
        try:
            for num in numbers:
                msg = client.messages.create(
                    body=alert,
                    from_=TWILIO_PHONE,
                    to=num
                )
            print("SMS sent successfully")
        except Exception as e:
            print(f"SMS failed: {e}")

    return jsonify({'alert': alert})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
