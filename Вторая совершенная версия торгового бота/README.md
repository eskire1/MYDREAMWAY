# Apex V5 Global

**Apex V5 Global** — модульная торговая система для алгоритмической торговли криптовалютами на бирже BingX.  
Система построена на ансамбле из пяти специализированных агентов, объединяет глубокое обучение (LSTM + Attention) и градиентный бустинг (CatBoost), а также включает механизмы онлайн-дообучения, строгого контроля рисков и развитую инфраструктуру логирования и бэктестинга.

---

## 🧠 Особенности системы

- **Иерархический ансамбль агентов**
  - **Hunter** – классификация рыночных состояний (LSTM + Attention)
  - **Critic** – статистический фильтр сигналов (ADX, спред, ликвидность, время)
  - **Strategist** – прогноз динамических целей (CatBoost Quantile Regression)
  - **Dispatcher** – управление капиталом и состоянием ордеров (Fixed Fractional Risk, High Water Mark Paranoia)
  - **Learner** – онлайн-дообучение моделей (Replay Buffer для нейросетей, инкрементальное обучение CatBoost)

- **Два специализированных индикатора на входе**
  - Композитный осциллятор (агрегация 30–50 классических индикаторов)
  - Зоны ликвидности (расстояние до уровней с аномальным объёмом)

- **Строгое управление рисками**
  - Динамическое плечо на основе волатильности (ATR‑50)
  - Режим «Паранойя» при просадке относительно High Water Mark
  - Конечный автомат сделки с Heartbeat‑таймаутом (защита от зависания)

- **Полноценный бэктестер**
  - Учёт проскальзывания, комиссий и задержки данных
  - Разметка сделок методом Triple‑Barrier

- **Гибкое логирование и хранение**
  - HDF5 для трёхмерных окон признаков
  - Parquet для логов Hunter и Strategist

---

## ⚙️ Требования

- Python 3.10+
- Установленные зависимости из `requirements.txt`

---

## 🚀 Установка

1. Клонируйте репозиторий:
   ```bash
   git clone <repo-url>
   cd apex_v5_global
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux / macOS
   venv\Scripts\activate         # Windows
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
4. Скопируйте шаблон переменных окружения и заполните его:
   ```bash
   cp .env.example .env
   # Укажите API ключи BingX и режим testnet

---

## 🔧 Конфигурация

Все параметры системы находятся в `config/settings.yaml`.
Основные секции:

- `general` – таймфрейм, символы, биржа
- `features` – размер окна, параметры нормализации
- `hunter` – архитектура LSTM, параметры дообучения
- `critic` – пороги фильтров
- `strategist` – параметры CatBoost, горизонт прогноза
- `dispatcher` – риск-менеджмент, режим паранойи
- `backtest` – комиссии, проскальзывание, задержка

При необходимости измените пути к данным и моделям в секции `paths`.

---

## 📊 Подготовка данных и обучение моделей

- **Исторические данные**

  Для обучения и бэктеста необходимы OHLCV-данные в формате CSV со столбцами:
`timestamp,open,high,low,close,volume`


- **Первичное обучение Hunter**
  ```bash
  python scripts/initial_train_hunter.py --data /path/to/historical.csv --config config/settings.yaml
  ```
  После завершения чекпоинт сохранится в `models/hunter/hunter_v1.ckpt`.

- **Первичное обучение Strategist**
    ```bash
    python scripts/initial_train_strategist.py --data /path/to/historical.csv --config config/settings.yaml
    ```
    Модель сохранится в `models/strategist/strategist_v1.cbm`.

> **Важно:** Для обучения используются индикаторы, реализованные в `src/data/indicators.py`. При необходимости замените заглушки на реальные расчёты.

---

## 📈 Запуск бэктеста

```bash
python scripts/run_backtest.py --data /path/to/historical.csv --config config/settings.yaml
```

В консоль будут выведены ключевые метрики:
- Количество сделок
- Win Rate
- Profit Factor
- Общий PnL
- Максимальная просадка
- Sharpe Ratio

---

## 🔴 Запуск live-торговли
```bash
python -m src.main
```

Система:
- Подключается к BingX (testnet / mainnet в зависимости от .env)
- Каждые 15 минут обрабатывает новую свечу
- Принимает решения через Hunter → Critic → Strategist → Dispatcher
- Логирует сигналы и сделки в HDF5 / Parquet
- Периодически запускает Learner для дообучения моделей

Для остановки используйте `Ctrl+C` – произойдёт graceful shutdown с закрытием всех хранилищ.

---

## 📁 Структура проекта

```text
apex_v5_global/
├── config/                     # YAML конфигурации
├── data/                       # Данные (raw, processed, logs)
├── models/                     # Сохранённые модели (hunter, strategist)
├── src/
│   ├── agents/                 # Агенты (hunter, critic, strategist, dispatcher, learner)
│   ├── data/                   # Индикаторы, препроцессинг, storage
│   ├── execution/              # Брокер, order manager, state machine
│   ├── backtest/               # Движок бэктеста
│   ├── utils/                  # Хелперы, логгер
│   └── main.py                 # Точка входа live-торговли
├── scripts/                    # Скрипты обучения и бэктеста
├── tests/                      # Модульные тесты
├── requirements.txt
├── README.md
└── .env.example
```

---

## 📝 Лицензия

Проект распространяется под лицензией MIT. Подробности см. в файле `LICENSE`.

Закреплено авторскими правами разработчика eskire1 .

---

**Apex V5 Global** — профессиональный инструмент для алгоритмической торговли, сочетающий современные методы машинного обучения и строгий риск-менеджмент.
Удачной торговли! 📊

``````