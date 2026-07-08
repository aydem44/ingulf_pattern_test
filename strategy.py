import pandas as pd
from datetime import datetime
import numpy as np

def calculating_signal(open_price, high, low, close, reward_risk):
    """
    Генерирует торговые сигналы на основе паттерна "поглощение".

    Args:
        open_price (pd.Series): Цены открытия.
        high (pd.Series): Максимальные цены.
        low (pd.Series): Минимальные цены.
        close (pd.Series): Цены закрытия.
        reward_risk (float): Коэффициент риск/прибыль.

    Returns:
        tuple[pd.Series, pd.Series, pd.Series]:
            - entry_flag: 1 (LONG), -1 (SHORT), 0 (нет сигнала)
            - stop_loss: Цена стоп-лосса на момент сигнала
            - take_profit: Цена тейк-профита на момент сигнала
    """
    n = len(close)
    entry_flag=pd.Series(0, index=close.index)
    stop_loss = pd.Series(np.nan, index=close.index)
    take_profit = pd.Series(np.nan, index=close.index)
    is_uptrend=pd.Series(False, index=close.index)
    
    # Вычисляем количество свечей в дне и задаем периоды для MA
    candles_per_day = 24 * 60 // 15  # 96
    ma20_period = 1 * candles_per_day 
    ma40_period = 5 * candles_per_day  

    # Проверяем, что данных достаточно для расчёта
    if len(close) < ma40_period:
        return entry_flag, stop_loss, take_profit

    for candle in range(1+ma40_period, n-1):
        # Расчёт MA прямо на данных 15-минутного таймфрейма
        ma20 = close.iloc[0:candle].rolling(ma20_period).mean().iloc[-1]
        ma40 = close.iloc[0:candle].rolling(ma40_period).mean().iloc[-1]
        is_uptrend.iloc[candle] = ma20 > ma40
        trend_factor=is_uptrend.iloc[candle]
    
        prev_open=open_price.iloc[candle-2].item()
        prev_close=close.iloc[candle-2].item()
        curr_open=open_price.iloc[candle-1].item()
        curr_close=close.iloc[candle-1].item()
        prev_bullish_candle = prev_open<prev_close
        prev_bearish_candle = prev_open>prev_close
        if prev_bearish_candle and curr_close>prev_open and trend_factor:
            entry_flag.iloc[candle]=1
            risk=curr_close - curr_open
            stop_loss.iloc[candle]=curr_open
            take_profit.iloc[candle] = curr_close + risk*reward_risk
        elif prev_bullish_candle and curr_close<prev_open and not trend_factor:
            entry_flag.iloc[candle]=-1
            risk=curr_open-curr_close
            stop_loss.iloc[candle]=curr_open
            take_profit.iloc[candle] = curr_close - risk*reward_risk
        else:
            entry_flag.iloc[candle]=0
            stop_loss.iloc[candle]=None
            take_profit.iloc[candle]=None
    
    return entry_flag, stop_loss, take_profit