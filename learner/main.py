from pymongo import MongoClient

import pandas as pd
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
# import category_encoders as ce
from sklearn.metrics import mean_squared_error as mse
from tensorflow import keras

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from tensorflow.keras.layers import Dense

import pandas as pd

def get_formatted_data():
    client = MongoClient("mongodb://mongoadmin:secret@mongo:27017/")
    db = client['device_data']
    collection = db['power_consumption']
    data = list(collection.find())
    data = pd.DataFrame(data)
    print(data.to_csv())
    data.drop(['_id'], axis=1, inplace=True)
    return data

df = get_formatted_data()

# print(df)

def week_status(day) -> int:
    if day.weekday() < 5:
        return 1
    else:
        return 0

df['WeekStatus'] = df['timestamp'].apply(week_status)
df['Day_of_week'] = df['timestamp'].dt.day_of_week
df['day'] = df['timestamp'].dt.day
df['month'] = df['timestamp'].dt.month
df['mean_temp'] = 10
df['workday'] = 0
df['power_usage'] = df['power_usage']

print(df)

summed_power = df.groupby(['day', 'month', 'year'])['power_usage'].sum()

# Renaming the columns to fit the required output format
summed_power.rename(columns={'power_usage': 'summed_power_usage'}, inplace=True)

data = summed_power

print(data)

# Usage_kWh	WeekStatus	Day_of_week	day	month	year	time	day_usage	holyday
data['previous_day_Usage_kWh'] = data['power_usage'].shift(96).fillna(84.77)

# WeekStatus	Day_of_week	day	month	workday	previous_day_Usage_kWh
y = data['power_usage']
X = data.drop(columns=['power_usage'])
X = X.corr()

print("X:")
print(X)

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
X_filtered_scalar = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_filtered_scalar, y, test_size = 0.3, random_state = 42)

from sklearn.metrics import mean_squared_error, r2_score

#Linear Regression Model
lr = LinearRegression()

from sklearn.preprocessing import PolynomialFeatures

poly = PolynomialFeatures(5)
X_poly_train = poly.fit_transform(X_train)
X_poly_test = poly.transform(X_test)

lr.fit(X_poly_train, y_train)

model = keras.Sequential()
model.add(Dense(20, activation='relu', input_shape=[len(X_poly_train[0])]))
model.add(Dense(20, activation='relu'))
model.add(Dense(1))

#compiling the model with adam optimiser and mse loss metrics
model.compile(optimizer= 'adam', loss='mse', metrics=['mse'])
history = model.fit(X_poly_train, y_train, epochs=500, verbose=0)

y_pred = model.predict(X_poly_test)
y_pred_dl = y_pred
print(f"Mean Squared Error: {mse(y_pred, y_test)}")
mse_dl = mean_squared_error(y_test, y_pred_dl)
rmse_dl = np.sqrt(mse_dl)
r2_dl = r2_score(y_test, y_pred_dl)
print(f"Deep Learning Model MSE: {mse_dl}, RMSE: {rmse_dl}, R²: {r2_dl}")

#visualization of the graph
x = y_test
y = y_pred
plt.title(f'Deep Learning Model', fontsize = 15, color = 'r', pad = 12)
plt.plot(x, y, 'o', color = 'r')

m, b = np.polyfit(x, y, 1)
plt.plot(x, m * x + b, color = 'darkblue')
plt.xlabel('Actual')
plt.ylabel('Predicted')
plt.show()