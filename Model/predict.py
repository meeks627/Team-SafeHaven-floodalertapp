# import dependencies
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
import pickle

# data processing
data = pd.read_csv('data/Lagos CSV')
data['time'] = pd.to_datetime(data['time'])

daily_data = data.resample('24h', on="time").agg({
    'prcp': 'sum',
    'rhum': 'mean',
    'drainage_score': 'mean',
    'elevation_score': 'mean'
})
daily_data['rain_24h'] = daily_data['prcp'].shift(1)
daily_data['rain_72h'] = daily_data['prcp'].rolling(window=3).sum().shift(1)
daily_data = daily_data.dropna()

# flood risk based on conditions
daily_data['flood'] = (
    (daily_data['rain_24h'] > 15) |  # Significant daily rain
    ((daily_data['rain_72h'] > 30) & (daily_data['rhum'] > 80)) # Accumulated saturation
).astype(int)
print("Class distribution (full dataset):\n", daily_data['flood'].value_counts())

features = [
    'rain_24h',
    'rain_72h',
    'rhum',
    'drainage_score',
    'elevation_score'
]
X = daily_data[features]
y = daily_data['flood']

# Train-test split with stratification
X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=41, shuffle=True
)

# Oversample training set and shuffling
_df_train = X_train.copy()
_df_train['flood'] = y_train.values
max_count = _df_train['flood'].value_counts().max()

_df_train_res = _df_train.groupby('flood', group_keys=False).apply(
    lambda x: x.sample(max_count, replace=True, random_state=41)
).reset_index(drop=True)


X_train_res = _df_train_res[features]
y_train_res = _df_train_res['flood']

X_train_res, y_train_res = shuffle(X_train_res, y_train_res, random_state=41)
print("Class distribution (train after resampling):\n", y_train_res.value_counts())

# Fit scaler on training set only, then transform test set
scaler = StandardScaler()
X_train_res[features] = scaler.fit_transform(X_train_res[features])
X_test[features] = scaler.transform(X_test[features])

# Use the resampled and shuffled training set for training
X_train, y_train = X_train_res, y_train_res


# Model definition
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=41
)

# Training
model.fit(X_train,y_train)
# Evaluation
y_pred = model.predict(X_test)
train_accuracy = model.score(X_train, y_train)
print(f'Training Accuracy: {train_accuracy:.2f}')
accuracy = accuracy_score(y_test, y_pred)
print(f'Model Accuracy: {accuracy:.2f}')

# Inference / Alert System
def alert_message(risk_prob):
    if risk_prob >= 0.8:
        alert = "HIGH RISK: Flood likely in next 6 hours. Evacuate."
    elif risk_prob >= 0.4:
        alert = "MODERATE RISK: Be on alert."
    else:
        alert = "LOW RISK"
    return f'Risk Probability: {risk_prob}\n {alert}'

# Testing on a Sample
sample = pd.DataFrame([{
    'rain_24h': 15,
    'rain_72h': 70,
    'rhum': 70,
    'drainage_score': 0.5,
    'elevation_score': 0.2
}])
sample[features] = scaler.transform(sample[features])

result = model.predict_proba(sample)[0,1]
print(alert_message(result))

# Deployment
with open('Model/flood_model.pkl', 'wb') as f:
    pickle.dump((model, scaler), f)