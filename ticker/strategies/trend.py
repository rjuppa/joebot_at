import json
import requests
import decimal
import numpy as np
import pandas as pd
from tabulate import tabulate
from decimal import Decimal

import os, sys

proj_path = "/Users/radekj/devroot/joebot/joebot_at"
# This is so Django knows where to find stuff.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.append(proj_path)

# This is so my local_settings.py gets loaded.
os.chdir(proj_path)

import django
django.setup()

import matplotlib
matplotlib.use('TkAgg')   # use for OSX

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
import statsmodels.api as sm
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from ticker.strategies.base import BaseStrategy
from trader.btc_trader import BTCTrader


def convert_ts(ts):
    return datetime.fromtimestamp(int(ts))


def get_trend(df, dt_start, dt_end, ax=None):
    """
    returns coef. A from equation y = A*x + B
    If A > 0 then trend goes UP
    If A < 0 then trend goes DOWN
    """
    x = df['jDate'][dt_start:dt_end]
    X1 = np.column_stack((x, x))
    X1 = sm.add_constant(X1)
    y1 = df['close'][dt_start:dt_end]
    fitted = sm.OLS(y1, X1).fit()
    if ax:
        ax.plot(df.index, fitted.fittedvalues, color='red')
    return fitted.params.x1 * 1000


def get_row_trend_15min(row):
    count = 3
    ts_end = int(row['date'])
    ts_start = ts_end - (300 * count)               # 1tick = 300 = 5min
    return get_trend(row.dataframe, convert_ts(ts_start), convert_ts(ts_end)) * 10000


def get_trend_15min(df, row):
    count = 3
    ts_end = int(row['date'])
    ts_start = ts_end - (300 * count)
    dt_start = convert_ts(ts_start)
    dt_end = convert_ts(ts_end)

    x = df['jDate'][dt_start:dt_end]
    X1 = np.column_stack((x, x))
    X1 = sm.add_constant(X1)
    y1 = df['close'][dt_start:dt_end]
    fitted = sm.OLS(y1, X1).fit()


class TrendStrategy(BaseStrategy):

    def get_trend(self, dt_start, dt_end, ax=None):
        """
        returns coef. A from equation y = A*x + B
        If A > 0 then trend goes UP
        If A < 0 then trend goes DOWN
        """
        x = self.market_data['jDate'][dt_start:dt_end]
        X1 = np.column_stack((x, x))
        X1 = sm.add_constant(X1)
        y1 = self.market_data['close'][dt_start:dt_end]
        fitted = sm.OLS(y1, X1).fit()
        if ax:
            ax.plot(self.market_data.index, fitted.fittedvalues, color='red')
        return fitted.params.x1 * 1000

    def get_row_trend_15min(self, row):
        count = 3
        ts_end = int(row['date'])
        ts_start = ts_end - (300 * count)               # 1tick = 300 = 5min
        return self.get_trend(convert_ts(ts_start), convert_ts(ts_end)) * 10000

    def get_lin_fit(self):
        x = np.array([0, 1, 2, 3])
        y = np.array([-1, 0.2, 0.9, 2.1])
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y)[0]
        print(m, c)
        plt.plot(x, y, 'o', label='Original data', markersize=10)
        plt.plot(x, m * x + c, 'r', label='Fitted line')



    def print_header(self):
        print(self.market_data.head(20))

    def count_trend(self):
        self.market_data['trend_15min'] = self.market_data.apply(self.get_row_trend_15min, axis=1)


def zscore(arr):
    n = len(arr)

    x = np.arange(1.0, n+1, 1.0)
    y = arr
    A = np.vstack([x, np.ones(len(x))]).T
    print(A)
    m, c = np.linalg.lstsq(A, y)[0]
    return m

if __name__ == "__main__":
    dt_end = datetime.strptime('2017-08-25 11:15:00', '%Y-%m-%d %H:%M:%S')
    dt_start = datetime.strptime('2017-08-25 08:00:00', '%Y-%m-%d %H:%M:%S')
    # dt_from = datetime.utcnow()
    bs = TrendStrategy('BTC_ETH')
    market_data = bs.read_data(dt_end, 1)
    #cc = market_data[['close', 'date']].copy()
    #cc['jDate'] = cc.index.to_julian_date()

    df = market_data.loc[dt_start: dt_end, :]
    df['x'] = df['date'] - 1503573000

    # df['trend'] = df['close'].rolling(5).apply(zscore)
    df['trend'] = pd.rolling_apply(df['close'], 5, lambda x: zscore(x))
    #df['trend_15min'] = df.apply(get_row_trend_15min, axis=1)
    print(df.head(50))

    #bs.print_header()

    fig, ax = plt.subplots()
    fig.set_size_inches(10, 8)
    ax.plot(market_data.index, market_data.close, color='gray')



    x = np.array(df.x)
    y = np.array(df.close)
    A = np.vstack([x, np.ones(len(x))]).T
    #print(A)
    #m, c = np.linalg.lstsq(A, y)[0]
    #print(m, c)
    #ax.plot(x, y, 'o', label='Original data', markersize=3)
    #ax.plot(x, m * x + c, 'r', label='Fitted line')


    #get_trend(market_data, dt_start, dt_end, ax)
    plt.show()
