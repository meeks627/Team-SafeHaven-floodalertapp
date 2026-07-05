import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             classification_report)
from sklearn.utils import shuffle
import pickle
import warnings
warnings.filterwarnings('ignore')

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

daily_data['flood'] = (
    (daily_data['rain_24h'] > 15) |
    ((daily_data['rain_72h'] > 30) & (daily_data['rhum'] > 80))
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

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=41
)

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

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_res)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=5,
    random_state=41,
    n_jobs=-1
)

model.fit(X_train_scaled, y_train_res)

y_pred = model.predict(X_test_scaled)
y_prob = model.predict_proba(X_test_scaled)[:, 1]

print("\n=== Model Evaluation ===")
print(f"Training Accuracy: {model.score(X_train_scaled, y_train_res):.4f}")
print(f"Test Accuracy:      {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision:          {precision_score(y_test, y_pred):.4f}")
print(f"Recall:             {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score:           {f1_score(y_test, y_pred):.4f}")
print(f"ROC-AUC:            {roc_auc_score(y_test, y_prob):.4f}")

cv_scores = cross_val_score(model, X_train_scaled, y_train_res, cv=5, scoring='roc_auc')
print(f"Cross-val ROC-AUC:  {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['No Flood', 'Flood']))

importances = model.feature_importances_
print("\nFeature Importances:")
for f, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
    print(f"  {f:20s} {imp:.4f}")


def alert_message(risk_prob):
    if risk_prob >= 0.8:
        alert = "HIGH RISK: Flood likely in next 6 hours. Evacuate."
    elif risk_prob >= 0.4:
        alert = "MODERATE RISK: Be on alert."
    else:
        alert = "LOW RISK"
    return f'Risk Probability: {risk_prob:.2%}\n{alert}'


sample = pd.DataFrame([{
    'rain_24h': 15,
    'rain_72h': 70,
    'rhum': 70,
    'drainage_score': 0.5,
    'elevation_score': 0.2
}])
sample_scaled = scaler.transform(sample[features])
result = model.predict_proba(sample_scaled)[0, 1]
print(f"\nSample inference:\n{alert_message(result)}")

with open('Model/flood_model.pkl', 'wb') as f:
    pickle.dump((model, scaler), f)
print("\nModel saved to Model/flood_model.pkl")
