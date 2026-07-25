"""
scripts/download_historical.py
Загружает исторические свечи с BingX (с пагинацией) и сохраняет в CSV для обучения/бэктеста.
Обрабатывает конец исторических данных без ошибки.
"""

import requests
import pandas as pd
import argparse
import time
from datetime import datetime

def fetch_klines(symbol: str, interval: str = "15m", limit: int = 1000,
                 end_time: int = None) -> pd.DataFrame:
    """
    Загружает свечи с BingX.
    :param symbol: торговая пара, например "BTC-USDT"
    :param interval: таймфрейм: 1m,5m,15m,1h,1d
    :param limit: количество свечей (макс. 1000)
    :param end_time: конец периода (timestamp в мс)
    :return: DataFrame с колонками timestamp, open, high, low, close, volume
    """
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {
        "symbol": symbol.replace("/", "-"),
        "interval": interval,
        "limit": limit
    }
    if end_time:
        params["endTime"] = end_time

    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()

    # Если данных нет (конец истории), возвращаем пустой DataFrame
    if data.get("code") == 100204:
        return pd.DataFrame()
    elif "data" not in data:
        raise Exception(f"BingX API error: {data}")

    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = pd.DataFrame(data["data"], columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "quote_volume", "trades"
    ])
    df = df[cols]
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-USDT", help="Торговая пара (например BTC-USDT)")
    parser.add_argument("--interval", default="15m", help="Таймфрейм: 1m,5m,15m,1h,1d")
    parser.add_argument("--output", default="../data/historical.csv", help="Путь для сохранения CSV")
    parser.add_argument("--limit", type=int, default=1000, help="Количество свечей за один запрос (макс 1000)")
    parser.add_argument("--sleep", type=float, default=0.1, help="Пауза между запросами (сек)")
    args = parser.parse_args()

    all_data = []
    end_time = int(datetime.now().timestamp() * 1000)
    request_count = 0

    print(f"Начинаем загрузку {args.symbol} {args.interval}...")

    while True:
        df = fetch_klines(args.symbol, args.interval, args.limit, end_time=end_time)
        if df.empty:
            print("Данные закончились.")
            break

        all_data.append(df)
        request_count += 1
        print(f"Запрос {request_count}: получено {len(df)} свечей (до {df['timestamp'].max()})")

        earliest_ts = int(df["timestamp"].min().timestamp() * 1000)
        if earliest_ts >= end_time:
            print("Нет более старых данных.")
            break

        end_time = earliest_ts - 1
        time.sleep(args.sleep)

    if not all_data:
        print("Не удалось загрузить ни одной свечи.")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    final_df = final_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    final_df.to_csv(args.output, index=False)
    print(f"Готово! Всего загружено {len(final_df)} свечей.")
    print(f"Файл сохранён: {args.output}")

if __name__ == "__main__":
    main()