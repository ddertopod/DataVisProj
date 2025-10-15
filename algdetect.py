import psycopg2
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter, medfilt
import statsmodels.api as sm
from CONFIG import Config

try:
    conn = psycopg2.connect(database = Config.DATABASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
    cursor = conn.cursor()
    cursor.execute("select calibrating_data from calibrating where deviceid_port like %s", ('433427026902051_%',))
    results = cursor.fetchall()
    
    input_values = []
    output_values = []
    for row in results:
        calibrating_data = row[0]
        if calibrating_data and isinstance(calibrating_data, list):
            for i in calibrating_data:
                input_values.append(i['input_value'])
                output_values.append(i['output_value'])
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()

interpolation_function = interp1d(input_values, output_values, kind='linear', fill_value="extrapolate")

try:
    cursor = conn.cursor()
    cursor.execute("select timestamp, can_data from messages where terminal_id = %s order by timestamp", ('433427026902051',))
    results = cursor.fetchall()
    
    timestamps = []
    lls = []
    for row in results:
        timestamp, can_data = row
        if can_data is not None and isinstance(can_data, dict) and 'LLS_0' in can_data:
            input_value = can_data['LLS_0']
            lls_value = interpolation_function(input_value)
            timestamps.append(datetime.fromtimestamp(timestamp))
            lls.append(lls_value)
except Exception as e:
    print(f"Ошибка при работе с PostgreSQL: {e}")

cursor.close()
conn.close()

frac = 0.05  
smoothed_values = sm.nonparametric.lowess(lls, np.arange(len(lls)), frac=frac)[:, 1]

threshold = 10  
rapid_change_duration = timedelta(minutes=10)  
events = []

i = 0
while i < len(smoothed_values) - 1:
    start_time = timestamps[i]
    start_volume = smoothed_values[i]
    cumulative_change = 0
    event_type = None
    j = i + 1

    while j < len(smoothed_values):
        change = smoothed_values[j] - smoothed_values[j - 1]
        cumulative_change += change
        if event_type is None:
            if cumulative_change > threshold:
                event_type = "Заправка"
            elif cumulative_change < -threshold:
                duration = timestamps[j] - start_time
                if duration <= rapid_change_duration:
                    event_type = "Слив"
                else:
                    cumulative_change = 0
                    break  
        if (event_type == "Заправка" and change < 0) or (event_type == "Слив" and change > 0):
            end_time = timestamps[j - 1]
            end_volume = smoothed_values[j - 1]
            if abs(end_volume - start_volume) >= threshold:
                events.append({
                    'type': event_type,
                    'start_time': start_time,
                    'end_time': end_time,
                    'volume_change': abs(end_volume - start_volume)
                })
            i = j - 1  
            break
        j += 1
    i += 1

plt.figure(figsize=(10, 6))
plt.plot(timestamps, smoothed_values, color='purple', label='Сглаженные данные')

for event in events:
    event_time = event['start_time'] if event['type'] == "Заправка" else event['end_time']
    event_volume = smoothed_values[timestamps.index(event_time)]
    annotation_text = f"{event['type']}: {event['volume_change']:.0f} л"
    plt.annotate(
        annotation_text,
        xy=(event_time, event_volume),
        xytext=(event_time, event_volume + 20),
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="green" if event['type'] == "Заправка" else "red", facecolor="white"),
        arrowprops=dict(arrowstyle="->", color="green" if event['type'] == "Заправка" else "red"),
        fontsize=10
    )

plt.xlabel('Время')
plt.ylabel('Объем в литрах')
plt.title('Зависимость объема в литрах от времени')
plt.legend(loc="upper left")
plt.grid(True)
plt.show()
