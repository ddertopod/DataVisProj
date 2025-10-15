import telebot
from datetime import datetime, timedelta
import psycopg2
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import statsmodels.api as sm
from telebot_calendar import CallbackData, Calendar, RUSSIAN_LANGUAGE
import os
from CONFIG import Config
from dotenv import load_dotenv
load_dotenv()
API = os.getenv("TELEAPI")
bot = telebot.TeleBot(API)
calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_callback = CallbackData("calendar", "action", "year", "month", "day")

DB_CONFIG = {
    "database": Config.DATABASE,
    "user": Config.USER,
    "password": Config.PASSWORD,
    "host": Config.HOST
}

user_data = {}
user_states = {}

def set_user_state(chat_id, state):
    user_states[chat_id] = state

def get_user_state(chat_id):
    return user_states.get(chat_id, None)

def reset_user_state(chat_id):
    user_states[chat_id] = None

def ensure_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {"start_time": None, "end_time": None, "selecting": None}
    else:
        user_data[chat_id].setdefault("start_time", user_data[chat_id].get("start_time"))
        user_data[chat_id].setdefault("end_time", user_data[chat_id].get("end_time"))
        user_data[chat_id].setdefault("selecting", user_data[chat_id].get("selecting"))

def connect_to_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None
    
@bot.message_handler(commands=['start'])
def handle_start(message):
    ensure_user_data(message.chat.id)
    user_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    user_markup.row('СТАРТ')
    global user_data
    user_data[message.chat.id] = {"start_time": None, "end_time": None}
    bot.reply_to(message, "Привет! Я бот для анализа показателей топлива в автомобилях.\n"
                          "Используй команды:\n"
                          "/load_ids - Загрузить доступные ID\n"
                          "/set_start_date - Выбрать начальную дату\n"
                          "/set_end_date - Выбрать конечную дату\n"
                          "/plot_fuel ID - Построить график остатка топлива\n"
                          "/plot_speed ID - Построить график скорости")

@bot.message_handler(commands=['load_ids'])
def load_ids(message):
    ensure_user_data(message.chat.id)
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT terminal_id FROM messages")
        ids = cursor.fetchall()
        cursor.close()
        conn.close()
        ids_list = [id_[0] for id_ in ids]
        chunk_size = 50
        for i in range(0, len(ids_list), chunk_size):
            chunk = ids_list[i:i + chunk_size]
            bot.send_message(message.chat.id, "\n".join(chunk))
    else:
        bot.reply_to(message, "Ошибка подключения к базе данных.")

@bot.message_handler(commands=['set_start_date', 'set_end_date'])
def set_date(message):
    global user_data
    ensure_user_data(message.chat.id)
    command = message.text.split()[0]  

    if command == "/set_start_date":
        user_data[message.chat.id]["selecting"] = "start_time"
        bot.send_message(message.chat.id, "Выберите начальную дату:")
    elif command == "/set_end_date":
        user_data[message.chat.id]["selecting"] = "end_time"
        bot.send_message(message.chat.id, "Выберите конечную дату:")

    today = datetime.now()
    markup = calendar.create_calendar(
        name=calendar_callback.prefix,
        year=today.year,
        month=today.month
    )
    bot.send_message(message.chat.id, "Выберите дату:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_callback.prefix))
def callback_calendar(call):
    global user_data
    name, action, year, month, day = call.data.split(calendar_callback.sep)
    try:
        selected_date = calendar.calendar_query_handler(bot, call, name, action, year, month, day)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass  
        else:
            raise
    if action == "DAY":
        selecting = user_data[call.message.chat.id].get("selecting")
        if selecting == "start_time":
            user_data[call.message.chat.id]["start_time"] = selected_date
            bot.send_message(call.message.chat.id, f"Начальная дата установлена: {selected_date.strftime('%Y-%m-%d')}")
        elif selecting == "end_time":
            user_data[call.message.chat.id]["end_time"] = selected_date
            bot.send_message(call.message.chat.id, f"Конечная дата установлена: {selected_date.strftime('%Y-%m-%d')}")

        user_data[call.message.chat.id]["selecting"] = None
        print(f"user_data после выбора даты: {user_data}")
    elif action == "CANCEL":
        bot.send_message(call.message.chat.id, "Выбор даты отменен.")

@bot.message_handler(commands=['plot_fuel'])
def plot_fuel_command(message):
    global user_data
    ensure_user_data(message.chat.id)
    chat_id = message.chat.id
    set_user_state(chat_id, "plot_fuel_waiting_for_id")  
    bot.send_message(chat_id, "Введите ID автомобиля для построения графика остатка топлива.")

@bot.message_handler(commands=['plot_speed'])
def plot_speed_command(message):
    global user_data
    ensure_user_data(message.chat.id)
    chat_id = message.chat.id
    set_user_state(chat_id, "plot_speed_waiting_for_id")  
    bot.send_message(chat_id, "Введите ID автомобиля для построения графика скорости.")

@bot.message_handler(func=lambda message: get_user_state(message.chat.id) in ["plot_fuel_waiting_for_id", "plot_speed_waiting_for_id"])
def process_id_input(message):
    global user_data
    chat_id = message.chat.id
    ensure_user_data(chat_id)
    user_id = message.text.strip()
    state = get_user_state(chat_id)
    if user_data.get(chat_id, {}).get("start_time") is None or user_data.get(chat_id, {}).get("end_time") is None:
        bot.send_message(chat_id, "Пожалуйста, сначала выберите даты с помощью /set_start_date и /set_end_date.")
        reset_user_state(chat_id) 
        return
    start_datetime = user_data[chat_id]["start_time"]
    end_datetime = user_data[chat_id]["end_time"]

    if state == "plot_fuel_waiting_for_id":
        plot_fuel(chat_id, user_id, start_datetime, end_datetime)
    elif state == "plot_speed_waiting_for_id":
        plot_speed(chat_id, user_id, start_datetime, end_datetime)

    reset_user_state(chat_id)  

def plot_fuel(chat_id, selected_id, start_datetime, end_datetime):
    conn = connect_to_db()
    if conn:
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
            bot.send_message(chat_id, f"Ошибка интерполяции: {e}")
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

            cursor.close()
            conn.close()
            
            if not timestamps or not lls:
                bot.send_message(chat_id, "Нет данных для выбранного интервала.")
                return

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
            plt.plot(timestamps, smoothed_values, label="Остаток топлива в баке")

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

            plt.xlabel("Время")
            plt.ylabel("Остаток топлива (л)")
            plt.title(f"Остаток топлива для ID: {selected_id}")
            plt.legend()
            plt.grid()
            file_name = "fuel_plot.png"
            plt.savefig(file_name)
            plt.close()
            if os.path.exists(file_name):
                print(f"Файл {file_name} успешно создан.")
            else:
                print(f"Ошибка: файл {file_name} не найден!")

            with open(file_name, 'rb') as photo:
                bot.send_photo(chat_id, photo)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при извлечении данных: {e}")
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")


def plot_speed(chat_id, selected_id, start_datetime, end_datetime):
    conn = connect_to_db()
    if conn:
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
            bot.send_message(chat_id, "Нет данных для выбранного интервала.")
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
            bot.send_message(chat_id, "Нет данных для построения графика.")
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
        file_name = "speed_plot.png"
        plt.savefig(file_name)
        plt.close()
        if os.path.exists(file_name):
            print(f"Файл {file_name} успешно создан.")
        else:
            print(f"Ошибка: файл {file_name} не найден!")


        with open(file_name, 'rb') as photo:
            bot.send_photo(chat_id, photo)
    else:
        bot.send_message(chat_id, "Ошибка подключения к базе данных.")

@bot.message_handler(func=lambda message: True)
def handle_unknown_messages(message):
    bot.send_message(message.chat.id, "Нажмите /start")

bot.polling(none_stop=True, interval=0) 