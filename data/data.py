from meteostat import Point, Hourly, Daily
from datetime import datetime
import pandas as pd
np.random.seed(42)

lagos = Point(6.5244,3.3792)
start = datetime(2015,1,1)
end = datetime.now()
data = Hourly(lagos,start,end).fetch()

data = data[['prcp','rhum']].dropna()
import numpy as np

# Randomized demo values (clipped between 0 and 1)
data['drainage_score'] = np.random.normal(loc=0.8, scale=0.05, size=len(data)).clip(0,1)
data['elevation_score'] = np.random.normal(loc=0.2, scale=0.05, size=len(data)).clip(0,1)


print(data.tail())
data.to_csv("Lagos CSV")