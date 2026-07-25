import ccxt, pandas as pd
exchange = ccxt.binance()
since = exchange.parse8601('2022-01-01T00:00:00Z')
all_klines = []
while since < exchange.parse8601('2023-01-01T00:00:00Z'):
    klines = exchange.fetch_ohlcv('ETH/USDT', '15m', since=since, limit=1000)
    if not klines: break
    all_klines += klines
    since = klines[-1][0] + 1
df = pd.DataFrame(all_klines, columns=['timestamp','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.to_csv('data/eth_2022.csv', index=False)