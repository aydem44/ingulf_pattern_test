#!/usr/bin/env python
# coding: utf-8

# In[1]:


import vectorbt as vbt
import pandas as pd
import numpy as np
import datetime
from time import sleep
import os
from dotenv import load_dotenv
from strategy import calculating_signal
from pybit.unified_trading import HTTP

# Решаем проблему связки европейского сервера с сервисами предоставления данных
load_dotenv()
proxy_login = os.getenv('PROXY_LOGIN')
proxy_password = os.getenv('PROXY_PASSWORD')
proxy_host = os.getenv('PROXY_HOST')
proxy_port = os.getenv('PROXY_PORT')
proxy_url = f"http://{proxy_login}:{proxy_password}@{proxy_host}:{proxy_port}"
os.environ['HTTP'] = proxy_url
os.environ['HTTPS'] = proxy_url


# In[ ]:


end_date = datetime.datetime.now()
session=HTTP(testnet=False,
    api_key=os.getenv('BYBIT_API_KEY'),
    api_secret=os.getenv('BYBIT_SECRET')
)


def multifetch_data_15m(symbol, days, interval):  
    """
    Загружает исторические данные с Bybit, разбивая запросы по 10 дней.

    Параметры:
    ----------
    symbol : str
        Торговая пара (например, 'BTCUSDT')
    days : int
        Количество дней для загрузки
    interval : str
        Таймфрейм (например, '15', '5', '1')

    Возвращает:
    ----------
    pd.DataFrame
        Данные с колонками Open, High, Low, Close, Volume, Turnover
    """
    output_df=pd.DataFrame()
    final_day = datetime.datetime.now()

    if days<=10:
        klines=session.get_kline(
            category='linear',
            symbol=symbol,
            interval = str(interval),
            start = int((final_day - datetime.timedelta(days=days)).timestamp()*1000),
            end = int(final_day.timestamp()*1000)
        )
        output_df=pd.DataFrame(klines.get('result').get('list'), columns=['datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
    else:
        days_shifting = days
        chunk_size=10
        while days_shifting>0:
            print(f"Осталось загрузить:{days_shifting} дней")
            sleep(1)
            klines=session.get_kline(
                category='linear',
                symbol=symbol,
                interval = str(interval),
                start = int((final_day - datetime.timedelta(days=days_shifting)).timestamp()*1000),
                end = int((final_day - datetime.timedelta(days=days_shifting-chunk_size)).timestamp()*1000)
            )
            temp_df = pd.DataFrame(klines.get('result').get('list'), columns=['datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
            output_df=pd.concat([output_df, temp_df]).drop_duplicates(keep='first')
            days_shifting = days_shifting - 10
            if days_shifting<chunk_size:
                chunk_size = days_shifting
    output_df['datetime'] = pd.to_datetime(output_df['datetime'].astype('int64'), unit='ms')
    output_df.set_index('datetime', inplace=True)
    output_df = output_df.astype('float64')
    output_df = output_df.sort_index()
    return output_df

btc_price = multifetch_data_15m('BTCUSDT', 1000, interval='15')


# In[ ]:


open_price = btc_price['Open']
high = btc_price['High']
low = btc_price['Low']
close = btc_price['Close']

EngulfingIndicator = vbt.IndicatorFactory(
    input_names = ['open_price', 'high', 'low', 'close'],
    param_names = ['reward_risk'],
    output_names = ['entry_flag', 'stop_loss','take_profit']
).from_apply_func(calculating_signal,
                  reward_risk = 1,
                  keep_pd=True
)

res = EngulfingIndicator.run(open_price, high, low, close,
    reward_risk=1)

pf = vbt.Portfolio.from_signals(
    close,
    entries = res.entry_flag==1,
    exits=None,
    short_entries = res.entry_flag==-1,
    short_exits=None,
    init_cash = 10000,
    size=0.1,
    sl_stop = res.stop_loss,
    tp_stop = res.take_profit,
    freq='1h'
)

print(pf.stats())
pf.plot().show()


# In[ ]:




