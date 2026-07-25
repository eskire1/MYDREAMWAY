import ccxt
import pandas as pd
import matplotlib.pyplot as plt
import requests
from matplotlib.animation import FuncAnimation
import time
import numpy as np


while True:

    APIKEY = 'OMeugH5rKkom0aW2js7bBye1sABaACZiaRbrgW9Qs81aTdTNkzzwre2TI5q6tnynKsidpQSvULeR5wmpw'
    SECRETKEY = '08hWBg86OqkD1wU6A9vekneR9u2dQO9wtP09aLnH5Zaz5tXuZmIYN8PoLGMCgpZshWD2Bpbvm5MDnvjyfhazQ'
    symbol = 'BTC/USDT:USDT'
    timeframe = '15m'

    lot_size = 0.01

    # Инициализация клиента BingX
    exchange = ccxt.bingx({
        'apiKey': APIKEY,
        'secret': SECRETKEY,
        'options': {
            'defaultType': 'swap',
        }
    })

    # Установление демо-режима
    exchange.set_sandbox_mode(True)


    if __name__ == '__main__':
        def get_data():
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
            #print(f"\nFull Data of Before Last Candle: {ohlcv[-2]}")
            #print(f"Before Last Candle: Open = {ohlcv[-2][1]}   Close = {ohlcv[-2][4]}\n\n")

            data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            #print("Full Data for last 500 candles:")
            #print(data)
            #print(f"\n\nAlso before last candle's low price: {data.iloc[-2][3]}\n\n")

            data['timestamp'] = pd.to_datetime(data['timestamp'])
            #print(f"\n\nModified data:\n{data}")

            data.set_index('timestamp',inplace=True)
            #print(f"\n\nModified data:\n{data}")

            return data


        def linreg(close, period):
            # Преобразуем входные данные в массив numpy
            close = np.array(close)
            # Создаем массив индексов для периодов - наша независимая переменная 'x' (время)
            x = np.arange(period)
            # Создаем массив для хранения значений линейной регрессии
            linreg_values = np.full_like(close, np.nan)

            # Вычисляем линейную регрессию для каждого значения 'y'
            for i in range(period - 1, len(close)):
                y = close[i - period + 1:i + 1]
                # Выполняем линейную регрессию
                # Стакуем два массива 'x' и массив единиц друг под другом и транспонируем,
                # чтобы получить матрицу 'period' x '2'
                A = np.vstack([x, np.ones(period)]).T
                # Используем метод наименьших квадратов, получаем большой кортеж данных,
                # Отбираем первое значение - массив множеств (или списков, там уже неважно)
                # И здесь 'm' - угол наклона, а 'c' - значение, так как формула нахождения 'y' такая: y = m * x + c,
                # где 'x' - наша независимая переменная (то есть время)
                m, c = np.linalg.lstsq(A, y, rcond=None)[0]
                # Сохраняем значение линейной регрессии
                linreg_values[i] = m * (period - 1) + c

            return linreg_values


        def calculate_relative_rate_of_values(values):
            # Проверка, что входной аргумент является одномерным массивом
            if not isinstance(values, (list, np.ndarray)) or (isinstance(values, np.ndarray) and np.array(values).ndim != 1):
                raise ValueError("Входные данные должны быть списком или массивом NumPy.")

            values = np.array(values)
            relative_rate = np.full_like(values, np.nan)
            #relative_rate = np.zeros(len(values) - 1)

            for i in range(1, len(values)): # Итерация идет от 1, потому что для вычисления текущего значения
                relative_rate[i] = (values[i] - values[i - 1]) / values[i - 1] * 1000 # нам требуется предыдущее значение

            return relative_rate

        '''
        def fetch_position_try():
            global flag_fig_close
            try:
                position = exchange.fetch_position(symbol=symbol)
            except ccxt.ExchangeError as e:
                print(f"\nОшибка при получении данных о позиции(ях): {e}\n")
                plt.close()
                flag_fig_close = 1
            
            return position
        '''


        flag = 0
        ax1 = None
        trailingStop = None
        timestamp_open_price = None
        previous_position = None
        last_position = None
        timestamp_trailing_stop = None
        flag_fig_close = 0


        def update(frame):
            global flag, ax1, trailingStop, timestamp_open_price, previous_position, last_position, timestamp_trailing_stop, flag_fig_close

            try:
                '''
                if flag == 1:
                    ax = plt.gca()
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    #print(f"xlim_ax: {xlim}\nylim_ax: {ylim}")
        
                    xlim1 = ax1.get_xlim()
                    ylim1 = ax1.get_ylim()
                '''


                data = get_data()
                print(f"Timestamp: {data.index.astype('int64')[-1] / 10000}")


                '''
                plt.clf()
                data['SMA_5'] = data['close'].rolling(window=5).mean()
                data['SMA_20'] = data['close'].rolling(window=20).mean()
        
                # Строим первый подграфик
                plt.subplot(2, 1, 1)
                plt.plot(data.index, data['close'], label='Close Price', color='blue')
                plt.plot(data.index, data['SMA_5'], label='SMA_5', color='orange')
                plt.plot(data.index, data['SMA_20'], label='SMA_20', color='green')
        
                plt.title('Close Price with Moving Averages')
                plt.xlabel('Time')
                plt.ylabel('Price')
                plt.legend()
        
                ax1 = plt.gca() # Получение и сохранение данных об осях 1-го подграфика
        
                if flag == 1:
                    ax1.set_xlim(xlim1)
                    ax1.set_ylim(ylim1)
                '''


                linreg_values = linreg(data['close'], 13)
                rerate_linreg_values = calculate_relative_rate_of_values(linreg_values)

                '''
                # Строим второй подграфик
                plt.subplot(2, 1, 2)
                plt.plot(data.index, rerate_linreg_values, label='Values of Linear Regression', color='lime')
        
                plt.title('Linear Regression')
                plt.xlabel('Time')
                plt.ylabel('Price')
                plt.legend()
        
                if flag == 1:
                    ax_new = plt.gca()
                    ax_new.set_xlim(xlim1)
                    ax_new.set_ylim(ylim)
        
                if flag == 0:
                    flag = 1
                '''


                # Здесь начинается алгоритм открытия и закрытия позиций
                #entryPrice = None
                number = ''.join(filter(str.isdigit, timeframe))  # Извлекаем все цифры
                unit = ''.join(filter(str.isalpha, timeframe))  # Извлекаем все буквы

                if number and unit:
                    number = int(number)  # Преобразуем строку в число
                    #print(f"\nTimeframe: число - {number}, временной интервал: {unit}\n")

                coeff = None

                def coeff_calculate(number, unit):
                    if unit == 'm':
                        return number
                    if unit == 'h':
                        number = number * 60
                        coeff_calculate(number, 'm')
                    if unit == 'd':
                        number = number * 24 * 60
                        coeff_calculate(number, 'm')
                    if unit == 'w':
                        number = number * 7 * 24 * 60
                        coeff_calculate(number, 'm')
                    if unit == 'M':
                        number = number * 30 * 24 * 60        # В этом месте мы взяли условно 30 дней за один месяц,
                        coeff_calculate(number, 'm')     # кажется, что сильно повлиять не должно, и, возможно,
                                                              # это будет нам даже на руку
                coeff = coeff_calculate(number, unit)

                offset = 0.0003 * coeff       # Здесь вместо '0.0003' было '0.0006'
                try:
                    position = exchange.fetch_position(symbol=symbol)
                    positions = exchange.fetch_positions()
                except ccxt.ExchangeError as e:
                    print(f"\nОшибка при получении данных о позиции(ях) (2): {e}\n")
                    plt.close()
                    flag_fig_close = 1

                # Short
                if (rerate_linreg_values[-2] - rerate_linreg_values[-1]) > 0.03 and (rerate_linreg_values[-2] - rerate_linreg_values[-3]) > 0.03 and rerate_linreg_values[-1] > rerate_linreg_values[-3]:
                    try:
                        #position = exchange.fetch_position(symbol=symbol)
                        if position['info'] == {} or position['info']['positionSide'] == 'LONG':
                            if len(positions) > 0:
                                try:
                                    previous_position = exchange.fetch_position(symbol=symbol)
                                except ccxt.ExchangeError as e:
                                    print(f"\nОшибка при получении данных о позиции(ях) (3): {e}\n")
                                    plt.close()
                                    flag_fig_close = 1

                                exchange.close_all_positions()

                            flag_you_can_open = 0
                            timestamp = data.index.astype('int64')[-1] / 10000
                            if timestamp != timestamp_trailing_stop:
                                flag_you_can_open = 1

                            if position['info'] == {} and len(positions) == 0 and flag_you_can_open == 1:
                                order = exchange.create_market_order(symbol=symbol, side='SELL', amount=lot_size, params={"positionSide": 'SHORT'})
                                print(f"\nОрдер {order['info']['side']} {order['info']['positionSide']} исполнен: {order}\n")

                                timestamp_open_price = data.index.astype('int64')[-1] / 10000
                                try:
                                    last_position = exchange.fetch_position(symbol=symbol)
                                except ccxt.ExchangeError as e:
                                    print(f"\nОшибка при получении данных о позиции(ях) (4): {e}\n")
                                    plt.close()
                                    flag_fig_close = 1

                                #position_new = exchange.fetch_position(symbol=symbol)
                                position_new = last_position
                                avgOpenPrice = float(position_new['info']['avgPrice'])
                                print(f"Средняя цена открытия позиции: {avgOpenPrice}\n")

                                entryPrice = avgOpenPrice
                                trailingStopDifference = entryPrice * offset
                                trailingStop = entryPrice + trailingStopDifference
                                print(f"Trailing-stop: {trailingStop}\n")


                    except Exception as e:
                        print("Ошибка при выполнении ордера: ", str(e))
                        print("Ответ API:", e.response if hasattr(e, 'response') else 'Нет ответа')

                # Long
                if (rerate_linreg_values[-1] - rerate_linreg_values[-2]) > 0.03 and (rerate_linreg_values[-3] - rerate_linreg_values[-2]) > 0.03 and rerate_linreg_values[-1] > rerate_linreg_values[-3]:
                    try:
                        #position = exchange.fetch_position(symbol=symbol)
                        if position['info'] == {} or position['info']['positionSide'] == 'SHORT':
                            if len(positions) > 0:
                                try:
                                    previous_position = exchange.fetch_position(symbol=symbol)
                                except ccxt.ExchangeError as e:
                                    print(f"\nОшибка при получении данных о позиции(ях) (5): {e}\n")
                                    plt.close()
                                    flag_fig_close = 1
                                exchange.close_all_positions()

                            flag_you_can_open = 0
                            timestamp = data.index.astype('int64')[-1] / 10000
                            if timestamp != timestamp_trailing_stop:
                                flag_you_can_open = 1

                            if position['info'] == {} and len(positions) == 0 and flag_you_can_open == 1:
                                order = exchange.create_market_order(symbol=symbol, side='BUY', amount=lot_size, params={"positionSide": 'LONG'})
                                print(f"\nОрдер {order['info']['side']} {order['info']['positionSide']} исполнен: {order}\n")

                                timestamp_open_price = data.index.astype('int64')[-1] / 10000
                                try:
                                    last_position = exchange.fetch_position(symbol=symbol)
                                except ccxt.ExchangeError as e:
                                    print(f"\nОшибка при получении данных о позиции(ях) (6): {e}\n")
                                    plt.close()
                                    flag_fig_close = 1

                                #position_new = exchange.fetch_position(symbol=symbol)
                                position_new = last_position
                                avgOpenPrice = float(position_new['info']['avgPrice'])
                                print(f"Средняя цена открытия позиции: {avgOpenPrice}\n")

                                entryPrice = avgOpenPrice
                                trailingStopDifference = entryPrice * offset
                                trailingStop = entryPrice - trailingStopDifference
                                print(f"Trailing-stop: {trailingStop}\n")

                    except Exception as e:
                        print("Ошибка при выполнении ордера: ", str(e))
                        print("Ответ API:", e.response if hasattr(e, 'response') else 'Нет ответа')

                '''
                # Фиксим таблички (которые появляются на время и пропадают)
                timestamp = data.index.astype('int64')[-1] / 10000
                if timestamp == timestamp_open_price:
        
                    # Для Short табличек
                    if last_position['info']['positionSide'] == 'SHORT':
                        if not((rerate_linreg_values[-2] - rerate_linreg_values[-1]) > 0.03 and (rerate_linreg_values[-2] - rerate_linreg_values[-3]) > 0.03):
                            exchange.close_all_positions()
        
                            if previous_position is not None and previous_position['info'] != {}:
        
                                side = None
                                if previous_position['info']['positionSide'] == 'SHORT':
                                    side = 'SELL'
                                elif previous_position['info']['positionSide'] == 'LONG':
                                    side = 'BUY'
        
                                order = exchange.create_market_order(symbol=symbol, side=side, amount=lot_size, params={"positionSide": previous_position['info']['positionSide']})
                                print(f"\nОрдер {order['info']['side']} {order['info']['positionSide']} исполнен: {order}\n")
                                print("Открыта позиция по предыдущему сигналу.\n")
        
                                timestamp_open_price = data.index.astype('int64')[-1] / 10000
                                last_position = exchange.fetch_position(symbol=symbol)
        
                                #position_new = exchange.fetch_position(symbol=symbol)
                                position_new = last_position
                                avgOpenPrice = float(position_new['info']['avgPrice'])
                                print(f"Средняя цена открытия позиции: {avgOpenPrice}\n")
        
                                entryPrice = avgOpenPrice
                                trailingStopDifference = entryPrice * offset
                                trailingStop = entryPrice - trailingStopDifference
                                print(f"Trailing-stop: {trailingStop}\n")
        
                    # Для Long табличек
                    if last_position['info']['positionSide'] == 'LONG':
                        if not((rerate_linreg_values[-1] - rerate_linreg_values[-2]) > 0.03 and (rerate_linreg_values[-3] - rerate_linreg_values[-2]) > 0.03):
                            exchange.close_all_positions()
        
                            if previous_position is not None and previous_position['info'] != {}:
        
                                side = None
                                if previous_position['info']['positionSide'] == 'SHORT':
                                    side = 'SELL'
                                elif previous_position['info']['positionSide'] == 'LONG':
                                    side = 'BUY'
        
                                order = exchange.create_market_order(symbol=symbol, side=side, amount=lot_size, params={"positionSide": previous_position['info']['positionSide']})
                                print(f"\nОрдер {order['info']['side']} {order['info']['positionSide']} исполнен: {order}\n")
                                print("Открыта позиция по предыдущему сигналу.\n")
        
                                timestamp_open_price = data.index.astype('int64')[-1] / 10000
                                last_position = exchange.fetch_position(symbol=symbol)
        
                                #position_new = exchange.fetch_position(symbol=symbol)
                                position_new = last_position
                                avgOpenPrice = float(position_new['info']['avgPrice'])
                                print(f"Средняя цена открытия позиции: {avgOpenPrice}\n")
        
                                entryPrice = avgOpenPrice
                                trailingStopDifference = entryPrice * offset
                                trailingStop = entryPrice - trailingStopDifference
                                print(f"Trailing-stop: {trailingStop}\n")
                '''

                # Trailing-Stop
                try:
                    position_last = exchange.fetch_position(symbol=symbol)
                except ccxt.ExchangeError as e:
                    print(f"\nОшибка при получении данных о позиции(ях) (7): {e}\n")
                    plt.close()
                    flag_fig_close = 1

                if position_last is not None and position_last['info'] != {}:

                    entryPrice = float(position_last['info']['avgPrice'])
                    trailingStopDifference = entryPrice * offset  # Разница trailing-stop'а
                    markPrice = float(position_last['info']['markPrice'])

                    # For Short
                    if position_last['info']['positionSide'] == 'SHORT':

                        if trailingStop is None:
                            trailingStop = entryPrice + trailingStopDifference

                        trailingStop_new = markPrice + trailingStopDifference
                        trailingStop = min(trailingStop, trailingStop_new)

                        if markPrice > trailingStop:
                            exchange.close_all_positions()
                            timestamp_trailing_stop = data.index.astype('int64')[-1] / 10000
                            print(f"\nПроизошло закрытие по trailing-stop'у. Trailing-Stop: {trailingStop}\n")

                    # For Long
                    if position_last['info']['positionSide'] == 'LONG':

                        if trailingStop is None:
                            trailingStop = entryPrice - trailingStopDifference

                        trailingStop_new = markPrice - trailingStopDifference
                        trailingStop = max(trailingStop, trailingStop_new)

                        if markPrice < trailingStop:
                            exchange.close_all_positions()
                            timestamp_trailing_stop = data.index.astype('int64')[-1] / 10000
                            print(f"\nПроизошло закрытие по trailing-stop'у. Trailing-Stop: {trailingStop}\n")

                if position_last is not None and position_last['info'] != {}:
                    print(f"Trailing-Stop for {position_last['info']['positionSide']} side: {trailingStop}\n")



            except ccxt.RequestTimeout as e:
                print(f"Таймаут запроса: {str(e)}. Попробуйте увеличить время ожидания.\n")
                plt.close()
                flag_fig_close = 1

            except ccxt.NetworkError as e:
                print(f"Сетевая ошибка: {str(e)}. Проверьте ваше интернет-соединение.\n")
                plt.close()
                flag_fig_close = 1

            except ccxt.ExchangeError as e:
                print(f"Ошибка на стороне биржи: {str(e)}. Проверьте настройки API или статус биржи.\n")
                plt.close()
                flag_fig_close = 1

            except requests.exceptions.ReadTimeout:
                print("Запрос превысил время ожидания. Попробуйте снова.\n")
                plt.close()
                flag_fig_close = 1

            except Exception as e:
                print(f"Произошла ошибка: {str(e)}. Попробуйте снова.\n")
                plt.close()
                flag_fig_close = 1







        print("\nБаланс демо-счета:")           # Вывод информации о демо-счете
        balance = exchange.fetch_balance()
        print(balance)         # (По сути всё сейчас должно работать)
        for currency, info in balance['total'].items():
            print(f"\n{currency}: {info}\n")


        ani = FuncAnimation(plt.gcf(), update, interval=6000, save_count=5)

        try:
            if flag_fig_close == 0:
                plt.show()  # Показываем график
        except KeyboardInterrupt:
            print("Программа остановлена вручную.")
            plt.close()
            flag_fig_close = 1

        #while plt.fignum_exists(1): # Проверяем, существует ли окно
        #    plt.pause(0)  # Пауза для обновления окна

    print("Начинается перезапуск. Пожалуйста подождите (15 секунд).\n")
    time.sleep(15)
