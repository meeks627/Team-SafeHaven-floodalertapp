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
import os
import warnings
warnings.filterwarnings('ignore')

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, 'flood_model.pkl')

FEATURES = [
    'rain_24h',
    'rain_72h',
    'rhum',
    'drainage_score',
    'elevation_score'
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Raw hourly data → daily features with rain_24h, rain_72h."""
    daily = df.resample('24h', on='time').agg({
        'prcp': 'sum',
        'rhum': 'mean',
        'drainage_score': 'mean',
        'elevation_score': 'mean'
    })
    daily['rain_24h'] = daily['prcp'].shift(1)
    daily['rain_72h'] = daily['prcp'].rolling(window=3).sum().shift(1)
    return daily.dropna()


def label_flood(df: pd.DataFrame) -> pd.Series:
    """Apply rule-based labeling, respecting manual actual_flood if present."""
    rule = (
        (df['rain_24h'] > 15) |
        ((df['rain_72h'] > 30) & (df['rhum'] > 80))
    ).astype(int)

    if 'actual_flood' in df.columns:
        manual = df['actual_flood'].notna()
        rule[manual] = df.loc[manual, 'actual_flood'].astype(int)

    return rule


def train_model(data: pd.DataFrame, save_path: str = MODEL_PATH) -> dict:
    """
    Train a Random Forest on the given data.
    Expects columns: time, prcp, rhum, drainage_score, elevation_score
    Returns dict of evaluation metrics.
    """
    if 'time' not in data.columns or 'prcp' not in data.columns:
        raise ValueError("Data must have 'time' and 'prcp' columns")

    daily = engineer_features(data)
    daily['flood'] = label_flood(daily)

    print("Class distribution (full dataset):\n", daily['flood'].value_counts())

    X = daily[FEATURES]
    y = daily['flood']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, test_size=0.2, random_state=41
    )

    _df_train = X_train.copy()
    _df_train['flood'] = y_train.values
    max_count = _df_train['flood'].value_counts().max()

    _df_train_res = _df_train.groupby('flood', group_keys=False).apply(
        lambda x: x.sample(max_count, replace=True, random_state=41)
    ).reset_index(drop=True)

    X_train_res = _df_train_res[FEATURES]
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

    metrics = {
        'train_accuracy': float(model.score(X_train_scaled, y_train_res)),
        'test_accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred)),
        'recall': float(recall_score(y_test, y_pred)),
        'f1': float(f1_score(y_test, y_pred)),
        'roc_auc': float(roc_auc_score(y_test, y_prob)),
        'samples': len(daily),
    }

    print("\n=== Model Evaluation ===")
    for k, v in metrics.items():
        if k != 'samples':
            print(f"{k:20s} {v:.4f}")
    print(f"{'samples':20s} {metrics['samples']}")

    cv_scores = cross_val_score(model, X_train_scaled, y_train_res, cv=5, scoring='roc_auc')
    print(f"Cross-val ROC-AUC:  {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Flood', 'Flood']))

    importances = model.feature_importances_
    print("\nFeature Importances:")
    for f, imp in sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True):
        print(f"  {f:20s} {imp:.4f}")

    with open(save_path, 'wb') as f:
        pickle.dump((model, scaler), f)
    print(f"\nModel saved to {save_path}")

    return metrics


def load_model(path: str = MODEL_PATH):
    with open(path, 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':
    csv_path = os.path.join(os.path.dirname(MODEL_DIR), 'data', 'Lagos CSV')
    data = pd.read_csv(csv_path)
    data['time'] = pd.to_datetime(data['time'])

    train_model(data)
