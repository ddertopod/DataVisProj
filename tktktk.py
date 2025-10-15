import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import psycopg2
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import statsmodels.api as sm
from CONFIG import Config

def connect_to_db():
    try:
        conn = psycopg2.connect(database = Config.DATABASE,
                                  user = Config.USER,
                                  password = Config.PASSWORD,
                                  host = Config.HOST)
        return conn
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных: {e}")
        return None

def load_all_ids():
    conn = connect_to_db()
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT terminal_id FROM messages")
        ids = cursor.fetchall()
        cursor.close()
        conn.close()
        
        id_combobox['values'] = [id_[0] for id_ in ids]
        messagebox.showinfo("Загрузка завершена", "Все уникальные ID автомобилей загружены.")

def plot_fuel_level():
    start_time = start_entry.get()
    end_time = end_entry.get()
    selected_id = id_combobox.get()
    
    if not selected_id or not start_time or not end_time:
        messagebox.showwarning("Предупреждение", "Пожалуйста, заполните все поля.")
        return

    try:
        start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты. Используйте YYYY-MM-DD HH:MM.")
        return
    
    conn = connect_to_db()
    if conn is not None:
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT calibrating_data FROM calibrating WHERE deviceid_port LIKE %s", (f'{selected_id}_%',))
            results = cursor.fetchall()
            
            input_values = []
            output_values = []
            
            for row in results:
                calibrating_data = row[0]
                if calibrating_data and isinstance(calibrating_data, list):
                    for entry in calibrating_data:
                        input_values.append(entry['input_value'])
                        output_values.append(entry['output_value'])

            interpolation_function = interp1d(input_values, output_values, kind='linear', fill_value="extrapolate")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить интерполяцию: {e}")
            cursor.close()
            conn.close()
            return

        try:
            cursor.execute("""
                SELECT timestamp, can_data->>'LLS_0' AS fuel_level
                FROM messages
                WHERE terminal_id = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """, (selected_id, start_datetime.timestamp(), end_datetime.timestamp()))
            
            results = cursor.fetchall()
            
            timestamps = []
            lls = []
            
            for row in results:
                ts = datetime.fromtimestamp(row[0])
                fuel_level_raw = row[1]
                if fuel_level_raw is not None:
                    lls_value = interpolation_function(float(fuel_level_raw))
                    timestamps.append(ts)
                    lls.append(lls_value)
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении данных: {e}")
            cursor.close()
            conn.close()
            return
        
        cursor.close()
        conn.close()
        
        if not results or not lls:
            messagebox.showinfo("Нет данных", "Данные для выбранного интервала не найдены.")
            return

        frac = 0.05 
        smoothed_values = sm.nonparametric.lowess(lls, np.arange(len(lls)), frac=frac)[:, 1]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, smoothed_values, label="Остаток топлива в баке")
        plt.xlabel("Время")
        plt.ylabel("Остаток топлива (л)")
        plt.title(f"Остаток топлива для ID: {selected_id}")
        plt.legend()
        plt.grid()
        plt.show()

def plot_speed_time():
    start_time = start_entry.get()
    end_time = end_entry.get()
    selected_id = id_combobox.get()
    
    if not selected_id or not start_time or not end_time:
        messagebox.showwarning("Предупреждение", "Пожалуйста, заполните все поля.")
        return
    
    try:
        start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты. Используйте YYYY-MM-DD HH:MM.")
        return
    
    conn = connect_to_db()
    if conn is not None:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, speed
            FROM messages
            WHERE terminal_id = %s AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp
        """, (selected_id, start_datetime.timestamp(), end_datetime.timestamp()))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            messagebox.showinfo("Нет данных", "Данные для выбранного интервала не найдены.")
            return

        timestamps = []
        speeds = []
        
        for row in results:
            ts = datetime.fromtimestamp(row[0])
            speed = row[1]
            if speed is not None:
                timestamps.append(ts)
                speeds.append(float(speed))

        if not timestamps or not speeds:
            messagebox.showinfo("Нет данных", "Нет данных для построения графика.")
            return
        
        frac = 0.05 
        smoothed_values = sm.nonparametric.lowess(speeds, np.arange(len(speeds)), frac=frac)[:, 1]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, smoothed_values, label="Скорость")
        plt.xlabel("Время")
        plt.ylabel("Скорость (км/ч)")
        plt.title(f"Скорость для ID: {selected_id}")
        plt.legend()
        plt.grid()
        plt.show()

root = tk.Tk()
root.title("Анализ данных автомобиля")

tk.Label(root, text="Дата/время начала и конец").grid(row=0, column=0, columnspan=2)
start_entry = tk.Entry(root, width=20)
start_entry.grid(row=1, column=0)
end_entry = tk.Entry(root, width=20)
end_entry.grid(row=1, column=1)
start_entry.insert(0, "2023-03-01 12:00")
end_entry.insert(0, "2023-03-05 12:00")

tk.Label(root, text="Выберите id:").grid(row=2, column=0, columnspan=2)
id_combobox = ttk.Combobox(root, width=25)
id_combobox.grid(row=3, column=0, columnspan=2)

load_ids_button = tk.Button(root, text="Все id автомобилей", command=load_all_ids)
load_ids_button.grid(row=4, column=0)

fuel_button = tk.Button(root, text="Остаток топлива в баке", command=plot_fuel_level)
fuel_button.grid(row=4, column=1)

speed_button = tk.Button(root, text="Скорость/время", command=plot_speed_time)
speed_button.grid(row=5, column=0, columnspan=2)

root.mainloop()
