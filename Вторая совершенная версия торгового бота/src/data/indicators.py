"""
src/data/indicators.py
Реализация двух специализированных индикаторов Apex V5 Global:
1. Композитный осциллятор (Composite Oscillator) — агрегация 19 классических индикаторов,
   выдающая три кривые: C_Long, C_Neutral, C_Short (значения 0-100).
   Дополнительно предоставляет все 19 индикаторов по отдельности для использования в Strategist.
2. Зоны ликвидности (Liquidity Zones) — полная информация о ближайших верхнем и нижнем
   уровнях поддержки/сопротивления на основе алгоритма LuxAlgo:
   - цена уровня
   - объём ликвидности (накопленный)
   - ширина зоны (high-low области свинга)
   - количество касаний
   - перекрытие ценой зоны (в пунктах и процентах)
Все данные возвращаются в формате словарей, готовых для использования в Hunter и Strategist.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
import warnings

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    warnings.warn("Library 'ta' not installed. Falling back to manual indicator calculations.")


# ------------------------------------------------------------------------------
# Композитный осциллятор (Индикатор №1)
# ------------------------------------------------------------------------------

@dataclass
class CompositeOscillatorResult:
    """Результат расчёта композитного осциллятора."""
    long: np.ndarray      # Кривая силы Long (0-100)
    neutral: np.ndarray   # Кривая силы Neutral (0-100)
    short: np.ndarray     # Кривая силы Short (0-100)


class CompositeOscillator:
    """Агрегирует выходы 19 классических индикаторов, выдаёт три сглаженные SMA(14) кривые
       и все промежуточные значения."""

    def __init__(self, num_indicators: int = 19):
        self.num_indicators = num_indicators

    def compute(self, df: pd.DataFrame) -> CompositeOscillatorResult:
        """Вычисляет сглаженные кривые Long/Neutral/Short."""
        n = len(df)
        if n < 50:
            zeros = np.zeros(n)
            return CompositeOscillatorResult(long=zeros, neutral=zeros, short=zeros)

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        signals = np.zeros((n, self.num_indicators), dtype=int)

        # Получаем все индикаторы
        indicators = self.get_all_indicators(df)

        # Сигналы по каждому индикатору
        signals[:, 0] = np.where(indicators['rsi'] < 30, 1, np.where(indicators['rsi'] > 70, -1, 0))
        macd_hist = indicators['macd_line'] - indicators['signal_line']
        signals[:, 1] = np.where(macd_hist > 0, 1, np.where(macd_hist < 0, -1, 0))
        signals[:, 2] = np.where(indicators['stoch_k'] < 20, 1, np.where(indicators['stoch_k'] > 80, -1, 0))
        signals[:, 3] = np.where(close < indicators['bb_lower'], 1, np.where(close > indicators['bb_upper'], -1, 0))
        signals[:, 4] = np.where(indicators['adx'] > 25, 1, 0)
        signals[:, 5] = np.where(indicators['vol_osc'] > 0, 1, -1)
        signals[:, 6] = np.where(indicators['atr'] > self._sma(indicators['atr'], 14), 1, 0)
        signals[:, 7] = np.where(indicators['zscore'] < -2, 1, np.where(indicators['zscore'] > 2, -1, 0))
        signals[:, 8] = np.where(indicators['corr'] > 0.8, 1, np.where(indicators['corr'] < -0.8, -1, 0))
        signals[:, 9] = np.where(indicators['cov'] > 0, 1, -1)
        signals[:, 10] = np.where(indicators['cci'] < -100, 1, np.where(indicators['cci'] > 100, -1, 0))
        signals[:, 11] = np.where(indicators['momentum'] > 0, 1, np.where(indicators['momentum'] < 0, -1, 0))
        signals[:, 12] = np.where(indicators['chande'] > 0, 1, np.where(indicators['chande'] < 0, -1, 0))
        signals[:, 13] = np.where(indicators['fib'] > 61.8, 1, np.where(indicators['fib'] < 38.2, -1, 0))
        signals[:, 14] = np.where(close > indicators['quantile'], 1, -1)
        signals[:, 15] = np.where(close > self._sma(close, 20), 1, -1)
        normal_z = (close - self._sma(close, 20)) / (self._rolling_std(close, 20) + 1e-10)
        signals[:, 16] = np.where(normal_z > 0, 1, -1)
        signals[:, 17] = np.where(indicators['sharpe'] > 1, 1, -1)
        signals[:, 18] = np.where(indicators['gauss_prob'] > 0.5, 1, -1)

        # Агрегация
        long_signals = np.sum(signals == 1, axis=1)
        short_signals = np.sum(signals == -1, axis=1)
        neutral_signals = self.num_indicators - long_signals - short_signals

        long_percent = (long_signals / self.num_indicators) * 100.0
        short_percent = (short_signals / self.num_indicators) * 100.0
        neutral_percent = (neutral_signals / self.num_indicators) * 100.0

        long_sma = self._sma(long_percent, 14)
        short_sma = self._sma(short_percent, 14)
        neutral_sma = self._sma(neutral_percent, 14)

        return CompositeOscillatorResult(
            long=long_sma,
            neutral=neutral_sma,
            short=short_sma
        )

    def get_all_indicators(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Возвращает словарь со всеми 19 индикаторами (и их компонентами) для каждого бара.
        Ключи:
        'rsi', 'macd_line', 'signal_line', 'stoch_k', 'bb_upper', 'bb_lower',
        'adx', 'vol_osc', 'atr', 'zscore', 'corr', 'cov', 'cci', 'momentum',
        'chande', 'fib', 'quantile', 'ml_signal', 'normal_z', 'sharpe', 'gauss_prob'.
        """
        n = len(df)
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        indicators = {}

        # 1. RSI(14)
        indicators['rsi'] = self._rsi(close, 14)

        # 2. MACD (12,26,9)
        macd_line, signal_line = self._macd(close, 12, 26, 9)
        indicators['macd_line'] = macd_line
        indicators['signal_line'] = signal_line

        # 3. Stochastic %K(14,3)
        indicators['stoch_k'] = self._stochastic(high, low, close, 14, 3)

        # 4. Bollinger Bands (20,2)
        bb_upper, bb_lower = self._bollinger_bands(close, 20, 2)
        indicators['bb_upper'] = bb_upper
        indicators['bb_lower'] = bb_lower

        # 5. ADX(14)
        indicators['adx'] = self._adx(high, low, close, 14)

        # 6. Volume Oscillator (разность SMA14 и SMA28 объёма)
        vol_sma14 = self._sma(volume, 14)
        vol_sma28 = self._sma(volume, 28)
        indicators['vol_osc'] = vol_sma14 - vol_sma28

        # 7. ATR(14)
        indicators['atr'] = self._atr(high, low, close, 14)

        # 8. Z-Score (20)
        indicators['zscore'] = self._zscore(close, 20)

        # 9. Correlation (сдвиг 20)
        indicators['corr'] = self._rolling_correlation(close, 20)

        # 10. Covariance (20)
        indicators['cov'] = self._rolling_covariance(close, 20)

        # 11. CCI (20)
        indicators['cci'] = self._cci(high, low, close, 20)

        # 12. Momentum (close - close[1])
        momentum = close - np.roll(close, 1)
        momentum[0] = 0
        indicators['momentum'] = momentum

        # 13. Chande Momentum Oscillator (14)
        indicators['chande'] = self._chande_momentum(close, 14)

        # 14. Fibonacci Retracement (50)
        indicators['fib'] = self._fibonacci_retracement(high, low, close, 50)

        # 15. Quantile (20, 0.5)
        indicators['quantile'] = self._rolling_quantile(close, 20, 0.5)

        # 16. ML Signal (SMA20)
        sma20 = self._sma(close, 20)
        indicators['ml_signal'] = np.where(close > sma20, 1.0, -1.0)

        # 17. Normal Distribution (Z-оценка относительно SMA20)
        indicators['normal_z'] = (close - sma20) / (self._rolling_std(close, 20) + 1e-10)

        # 18. Sharpe Ratio (14)
        indicators['sharpe'] = self._rolling_sharpe(close, 14)

        # 19. Gaussian Probability
        indicators['gauss_prob'] = self._gaussian_probability(close, 20)

        return indicators

    # --------------------------------------------------------------------------
    # Статические методы расчёта (сохранены без изменений)
    # --------------------------------------------------------------------------
    @staticmethod
    def _sma(x: np.ndarray, period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.trend.sma_indicator(pd.Series(x), period).fillna(0).values
        out = np.full_like(x, np.nan)
        for i in range(period-1, len(x)):
            out[i] = np.mean(x[i-period+1:i+1])
        return out

    @staticmethod
    def _ema(x: np.ndarray, period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.trend.ema_indicator(pd.Series(x), period).fillna(0).values
        out = np.zeros_like(x)
        alpha = 2.0 / (period + 1)
        out[0] = x[0]
        for i in range(1, len(x)):
            out[i] = alpha * x[i] + (1 - alpha) * out[i-1]
        return out

    @staticmethod
    def _rsi(close: np.ndarray, period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.momentum.rsi(pd.Series(close), period).fillna(50).values
        delta = np.diff(close, prepend=close[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = CompositeOscillator._sma(gain, period)
        avg_loss = CompositeOscillator._sma(loss, period)
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _macd(close: np.ndarray, fast: int, slow: int, signal: int):
        ema_fast = CompositeOscillator._ema(close, fast)
        ema_slow = CompositeOscillator._ema(close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = CompositeOscillator._ema(macd_line, signal)
        return macd_line, signal_line

    @staticmethod
    def _stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int, d_period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.momentum.stoch(pd.Series(high), pd.Series(low), pd.Series(close), k_period, d_period).fillna(50).values
        lowest_low = pd.Series(low).rolling(k_period).min().values
        highest_high = pd.Series(high).rolling(k_period).max().values
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        stoch_k = np.nan_to_num(stoch_k, nan=50)
        return CompositeOscillator._sma(stoch_k, d_period)

    @staticmethod
    def _bollinger_bands(close: np.ndarray, period: int, std_dev: float):
        sma = CompositeOscillator._sma(close, period)
        std = CompositeOscillator._rolling_std(close, period)
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        return upper, lower

    @staticmethod
    def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.trend.adx(pd.Series(high), pd.Series(low), pd.Series(close), period).fillna(20).values
        tr = np.maximum(high - low, np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1)))
        atr = CompositeOscillator._ema(tr, period)
        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        plus_di = 100 * CompositeOscillator._ema(plus_dm, period) / (atr + 1e-10)
        minus_di = 100 * CompositeOscillator._ema(minus_dm, period) / (atr + 1e-10)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = CompositeOscillator._ema(dx, period)
        return adx

    @staticmethod
    def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        if TA_AVAILABLE:
            return ta.volatility.average_true_range(pd.Series(high), pd.Series(low), pd.Series(close), period).fillna(0).values
        tr = np.maximum(high - low, np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1)))
        atr = CompositeOscillator._ema(tr, period)
        return atr

    @staticmethod
    def _zscore(x: np.ndarray, period: int) -> np.ndarray:
        sma = CompositeOscillator._sma(x, period)
        std = CompositeOscillator._rolling_std(x, period)
        return (x - sma) / (std + 1e-10)

    @staticmethod
    def _rolling_std(x: np.ndarray, period: int) -> np.ndarray:
        return pd.Series(x).rolling(period).std().fillna(0).values

    @staticmethod
    def _rolling_correlation(x: np.ndarray, period: int) -> np.ndarray:
        return pd.Series(x).rolling(period).corr(pd.Series(x).shift(period)).fillna(0).values

    @staticmethod
    def _rolling_covariance(x: np.ndarray, period: int) -> np.ndarray:
        return pd.Series(x).rolling(period).cov(pd.Series(x).shift(period)).fillna(0).values

    @staticmethod
    def _cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        tp = (high + low + close) / 3
        sma_tp = CompositeOscillator._sma(tp, period)
        mean_dev = pd.Series(np.abs(tp - sma_tp)).rolling(period).mean().fillna(1).values
        cci = (tp - sma_tp) / (0.015 * mean_dev + 1e-10)
        return cci

    @staticmethod
    def _chande_momentum(close: np.ndarray, period: int) -> np.ndarray:
        diff = close - np.roll(close, period)
        diff[0:period] = 0
        abs_diff = np.abs(close - np.roll(close, period))
        abs_diff[0:period] = 0
        sma_diff = CompositeOscillator._sma(diff, period)
        sma_abs = CompositeOscillator._sma(abs_diff, period)
        return 100 * sma_diff / (sma_abs + 1e-10)

    @staticmethod
    def _fibonacci_retracement(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        highest = pd.Series(high).rolling(period).max().values
        lowest = pd.Series(low).rolling(period).min().values
        return 100 * (close - lowest) / (highest - lowest + 1e-10)

    @staticmethod
    def _rolling_quantile(x: np.ndarray, period: int, q: float) -> np.ndarray:
        return pd.Series(x).rolling(period).quantile(q).bfill().fillna(0).values

    @staticmethod
    def _rolling_sharpe(close: np.ndarray, period: int) -> np.ndarray:
        ret = np.diff(close) / (close[:-1] + 1e-10)
        ret = np.insert(ret, 0, 0)
        mean_ret = pd.Series(ret).rolling(period).mean().fillna(0).values
        std_ret = pd.Series(ret).rolling(period).std().fillna(1).values
        return mean_ret / (std_ret + 1e-10)

    @staticmethod
    def _gaussian_probability(close: np.ndarray, period: int) -> np.ndarray:
        sma = CompositeOscillator._sma(close, period)
        std = CompositeOscillator._rolling_std(close, period) + 1e-10
        z = (close - sma) / std
        prob = np.exp(-0.5 * z**2) / (std * np.sqrt(2 * np.pi))
        return prob


# ------------------------------------------------------------------------------
# Индикатор зон ликвидности (Индикатор №2) – полная информация
# ------------------------------------------------------------------------------

class LiquidityZones:
    """
    Определяет зоны ликвидности на основе свинговых точек и объёма.
    Возвращает для каждого бара словари с полными данными по ближайшим верхнему и нижнему
    уровням: цена, объём ликвидности, ширина зоны, количество касаний, перекрытие (пункты, %).
    """

    def __init__(self, pivot_lookback: int = 14, volume_percentile: float = 90):
        self.pivot_lookback = pivot_lookback
        self.volume_percentile = volume_percentile
        self.upper_levels = []  # список словарей {'price': float, 'volume': float, 'width': float}
        self.lower_levels = []

    def identify_levels(self, df: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
        """Находит свинговые уровни с аномальным объёмом."""
        n = len(df)
        if n < 2 * self.pivot_lookback:
            return [], []

        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        from scipy.signal import argrelextrema
        high_peaks = argrelextrema(high, np.greater, order=self.pivot_lookback)[0]
        low_peaks = argrelextrema(low, np.less, order=self.pivot_lookback)[0]

        upper_candidates = []
        for idx in high_peaks:
            if idx < n:
                width = df.iloc[idx]['high'] - df.iloc[idx]['low']
                upper_candidates.append({
                    'price': float(high[idx]),
                    'volume': float(volume[idx]),
                    'width': width
                })

        lower_candidates = []
        for idx in low_peaks:
            if idx < n:
                width = df.iloc[idx]['high'] - df.iloc[idx]['low']
                lower_candidates.append({
                    'price': float(low[idx]),
                    'volume': float(volume[idx]),
                    'width': width
                })

        if upper_candidates:
            vols = [u['volume'] for u in upper_candidates]
            thresh_upper = np.percentile(vols, self.volume_percentile) if vols else 0
            self.upper_levels = [u for u in upper_candidates if u['volume'] >= thresh_upper]
        else:
            self.upper_levels = []

        if lower_candidates:
            vols = [l['volume'] for l in lower_candidates]
            thresh_lower = np.percentile(vols, self.volume_percentile) if vols else 0
            self.lower_levels = [l for l in lower_candidates if l['volume'] >= thresh_lower]
        else:
            self.lower_levels = []

        for level in self.upper_levels:
            level['count'] = 1
        for level in self.lower_levels:
            level['count'] = 1

        return self.upper_levels, self.lower_levels

    def _find_nearest(self, price: float, levels: List[Dict]) -> Optional[Dict]:
        if not levels:
            return None
        return min(levels, key=lambda lvl: abs(lvl['price'] - price))

    def compute_series(self, df: pd.DataFrame, atr_series: np.ndarray) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Возвращает словари с полными данными ликвидности для каждого бара."""
        n = len(df)
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        liq_upper_data = {
            'price': np.full(n, np.nan),
            'volume': np.full(n, np.nan),
            'width': np.full(n, np.nan),
            'count': np.full(n, np.nan),
            'overlap_pts': np.full(n, np.nan),
            'overlap_pct': np.full(n, np.nan)
        }
        liq_lower_data = {
            'price': np.full(n, np.nan),
            'volume': np.full(n, np.nan),
            'width': np.full(n, np.nan),
            'count': np.full(n, np.nan),
            'overlap_pts': np.full(n, np.nan),
            'overlap_pct': np.full(n, np.nan)
        }

        if not self.upper_levels and not self.lower_levels:
            self.identify_levels(df)

        for i in range(n):
            current_price = close[i]

            # Верхний уровень
            upper_above = [lvl for lvl in self.upper_levels if lvl['price'] >= current_price]
            if upper_above:
                nearest_upper = min(upper_above, key=lambda lvl: lvl['price'] - current_price)
            else:
                nearest_upper = self._find_nearest(current_price, self.upper_levels)

            if nearest_upper:
                liq_upper_data['price'][i] = nearest_upper['price']
                liq_upper_data['volume'][i] = nearest_upper['volume']
                liq_upper_data['width'][i] = nearest_upper['width']
                liq_upper_data['count'][i] = nearest_upper.get('count', 1)
                overlap_pts = max(0, high[i] - nearest_upper['price'])
                liq_upper_data['overlap_pts'][i] = overlap_pts
                liq_upper_data['overlap_pct'][i] = (overlap_pts / nearest_upper['width'] * 100) if nearest_upper['width'] > 0 else 0.0

            # Нижний уровень
            lower_below = [lvl for lvl in self.lower_levels if lvl['price'] <= current_price]
            if lower_below:
                nearest_lower = min(lower_below, key=lambda lvl: current_price - lvl['price'])
            else:
                nearest_lower = self._find_nearest(current_price, self.lower_levels)

            if nearest_lower:
                liq_lower_data['price'][i] = nearest_lower['price']
                liq_lower_data['volume'][i] = nearest_lower['volume']
                liq_lower_data['width'][i] = nearest_lower['width']
                liq_lower_data['count'][i] = nearest_lower.get('count', 1)
                overlap_pts = max(0, nearest_lower['price'] - low[i])
                liq_lower_data['overlap_pts'][i] = overlap_pts
                liq_lower_data['overlap_pct'][i] = (overlap_pts / nearest_lower['width'] * 100) if nearest_lower['width'] > 0 else 0.0

        return liq_upper_data, liq_lower_data