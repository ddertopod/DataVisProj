# DataVisProj

Проект **DataVisProj** — это комплекс визуализации и анализа телематических данных транспортных средств с интеграцией PostgreSQL, интерфейсом Tkinter и Telegram‑ботом.

## Состав проекта

```
DataVisProj/
├── CONFIG.py                  # Конфигурация подключения к БД
├── Makefile                   # Автоматизация загрузки данных, установки и запуска
├── requirements.txt            # Список зависимостей Python
├── preparation1.py             # Создание БД
├── preparation2.py             # Создание таблицы messages
├── preparation3.py             # Загрузка данных test.csv
├── preparation4.py             # Создание таблицы calibrating
├── preparation5.py             # Загрузка данных calib2.csv
├── tktktk.py                   # GUI‑интерфейс на Tkinter
├── algdetect.py                # Анализ и визуализация показателей
├── preparationNEWNEWNEW.py     # Тест бота
└── tgbotfinal.py               # Финальная логика Telegram‑бота
```

## Установка

### 1. Установить зависимости системы
Для Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk postgresql postgresql-contrib libpq-dev
```

### 2. Клонировать проект и перейти в каталог
```bash
git clone <repo_url>
cd DataVisProj
```

### 3. Установить зависимости Python
```bash
make install
```
или если есть ошибки то запускать из под sudo:
```bash
sudo pip install -r requirements.txt
```

### 4. Настроить окружение
Создай файл `.env` в корне проекта:
```
TELEAPI=***
```
Здесь укажите API вашего созданного тг бота

В файле CONFIG.py поменять имя пользователя, пароль и хост на свой!!!

## Подготовка базы данных

Для начала нужно загрузить данные вручную:
```bash
make download
```

Для автоматической подготовки структуры и загрузки CSV:
```bash
make prepare
```
Выполняются поочередно скрипты:
1. `preparation1.py` — создаёт БД `bigdata`
2. `preparation2.py` — создаёт таблицу `messages`
3. `preparation3.py` — загружает `data/test.csv`
4. `preparation4.py` — создаёт таблицу `calibrating`
5. `preparation5.py` — загружает `data/calib2.csv`


## Модули проекта

### Tkinter GUI
Графический интерфейс для анализа данных.
```bash
make tk
```
или:
```bash
python3 tktktk.py
```
Позволяет:
- загружать ID автомобилей,
- отображать график уровня топлива по датам,
- интерполировать данные калибровки.

### Анализ данных
```bash
make test
```
или:
```bash
python3 algdetect.py
```
Модуль анализирует изменения уровня топлива и определяет события **заправок** и **сливов**.

Результат визуализируется графиком (в GUI‑режиме) или сохраняется в файл.

### Telegram‑бот
Бот обеспечивает доступ к данным и построению графиков через Telegram.

Запуск:
```bash
make telebot
```
Он выполняет:
`tgbotfinal.py` — запуск основного функционала бота.

Основные команды:
- `/start` — приветствие и список команд;
- `/load_ids` — список ID;
- `/set_start_date`, `/set_end_date` — выбор дат;
- `/plot_fuel ID`, `/plot_speed ID` — построение графиков топлива и скорости.

## Полезные команды Makefile

| Команда | Назначение |
|----------|------------|
| `make install` | установка зависимостей |
| `make download` | скачивание CSV файлов в `data/` |
| `make prepare` | полная подготовка БД |
| `make tk` | запуск Tkinter GUI |
| `make test` | анализ данных |
| `make telebot` | запуск Telegram‑бота |
| `make clean` | очистка данных |

---
Автор: **Ddertopod**  
