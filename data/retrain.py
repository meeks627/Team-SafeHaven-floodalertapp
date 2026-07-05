import os
import sys
import pandas as pd
from datetime import datetime

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import data.ingest as ingest
from Model.predict import train_model, FEATURES

LOG_PATH = os.path.join(_script_dir, 'training_log.csv')
MODEL_PATH = os.path.join(_project_root, 'Model', 'flood_model.pkl')


def run_retrain():
    print("=" * 50)
    print(f"Retrain started at {datetime.now().isoformat()}")
    print("=" * 50)

    iot_df = ingest.get_all_readings()
    hist_df = ingest.get_historical_data()

    print(f"IoT records in DB: {len(iot_df)}")
    print(f"Historical records from CSV: {len(hist_df)}")

    combined = pd.concat([hist_df, iot_df], ignore_index=True)

    if 'time' not in combined.columns and 'recorded_at' in combined.columns:
        combined.rename(columns={'recorded_at': 'time'}, inplace=True)

    if 'prcp' not in combined.columns:
        combined['prcp'] = combined['rain_24h']

    combined['time'] = pd.to_datetime(combined['time'])

    metrics = train_model(combined, save_path=MODEL_PATH)

    metrics['timestamp'] = datetime.now().isoformat()
    metrics['iot_records'] = len(iot_df)
    metrics['historical_records'] = len(hist_df)

    log_row = pd.DataFrame([metrics])
    if os.path.exists(LOG_PATH):
        log_row.to_csv(LOG_PATH, mode='a', header=False, index=False)
    else:
        log_row.to_csv(LOG_PATH, index=False)

    print(f"\nMetrics logged to {LOG_PATH}")
    print("Retrain complete.\n")

    return metrics


if __name__ == '__main__':
    run_retrain()
