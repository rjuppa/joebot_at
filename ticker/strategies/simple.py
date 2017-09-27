import json
import requests
import decimal
import numpy as np
import pandas as pd
from tabulate import tabulate
from decimal import Decimal

import os, sys

proj_path = "/home/radekj/devroot/joebot_at"
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


def get_trend2(df, dt_start, dt_end, ax=None):
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
        ax.plot(x, fitted.fittedvalues, color='red')
    return fitted.params.x1 * 1000


def convert_ts(ts):
    return datetime.fromtimestamp(int(ts))


def get_trend(arr):
    n = len(arr)
    x = np.arange(1.0, n+1, 1.0)
    y = arr
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]
    return m


def get_color(arr):
    if min(arr) == 1:
        return 1
    if max(arr) == -1:
        return -1
    return 0


class SimpleStrategy(BaseStrategy):

    def get_precolor(self, row):
        return -1 if row.close < row.ema_hour else 1

    def get_final_color(self, row):
        if row.color_0 == 0:
            if row.trend_1h > 0:
                return 1
            else:
                return -1
        return row.color_0

    def get_color(self, row):
        return 1 if row.ema_hour_trend > 0 else -1


    def calculate_signal(self, is_print=False):
        """
        Calculating all helper data columns
        Mostly based on exponential weighted mean and other rolling functions
        EMA and difference
        """
        self.market_data['jDate'] = self.market_data.index.to_julian_date()
        self.market_data['ema_hour'] = self.market_data['close'].ewm(span=12, adjust=False).mean()
        self.market_data['ema_hour_trend'] = pd.rolling_apply(self.market_data['ema_hour'], 3, lambda x: get_trend(x))
        self.market_data['ema_12hours'] = self.market_data['close'].ewm(span=72, adjust=False).mean()
        self.market_data['ema_12hours_trend'] = pd.rolling_apply(self.market_data['ema_12hours'], 3,
                                                              lambda x: get_trend(x))
        self.market_data['ema_day'] = self.market_data['close'].ewm(span=self.prices_in_a_day,
                                                                    adjust=False).mean()
        self.market_data['ema_day_trend'] = pd.rolling_apply(self.market_data['ema_day'], 3,
                                                              lambda x: get_trend(x))

        self.market_data['ema_week'] = self.market_data['close'].ewm(span=self.prices_in_a_day * 7,
                                                                     adjust=False).mean()
        self.market_data['ema_month'] = self.market_data['close'].ewm(span=self.prices_in_a_day * 30,
                                                                      adjust=False).mean()
        #self.market_data['trend_day'] = pd.rolling_apply(self.market_data['close'], 288, lambda x: get_trend(x))
        self.market_data['trend_4h'] = pd.rolling_apply(self.market_data['close'], 48, lambda x: get_trend(x))
        self.market_data['trend_1h'] = pd.rolling_apply(self.market_data['close'], 12, lambda x: get_trend(x))
        self.market_data['trend_30min'] = pd.rolling_apply(self.market_data['close'], 6, lambda x: get_trend(x))
        self.market_data['trend_15min'] = pd.rolling_apply(self.market_data['close'], 3, lambda x: get_trend(x))

        self.market_data['max_15min'] = self.market_data['close'].rolling(window=3).max()
        self.market_data['max_30min'] = self.market_data['close'].rolling(window=6).max()

        #self.market_data['pre_color'] = self.market_data.apply(self.get_precolor, axis=1)
        #self.market_data['color_0'] = pd.rolling_apply(self.market_data['pre_color'], 5, lambda x: get_color(x))
        #self.market_data['color'] = self.market_data.apply(self.get_final_color, axis=1)
        self.market_data['color'] = self.market_data.apply(self.get_color, axis=1)

        self.market_data['ema5'] = self.market_data['close'].ewm(5).mean()
        self.market_data['buy_line'] = self.market_data['ema5'].mean()

        return super(SimpleStrategy, self).calculate_signal(is_print)

    def get_signal_buy(self, row):
        """ Handle BUY conditions """
        if row.ema_12hours_trend > 0 and row.ema_day_trend > -0.000007:
            if row.close < row.ema_month * 0.99:
                if row.close < row.ema_week * 0.99:
                    if row.close < row.ema_day * 0.99:
                        if row.trend_15min > 0:
                            #print(row)
                            return self.execute_buy(row)

        # if row.close < row.ema_day:
        #     if row.trend_15min > 0 and row.trend_30min > 0:
        #         return self.execute_buy(row)

    def get_signal_sell(self, row):
        """ Handle SELL conditions """
        if row.close > row.ema_day * 1.00:
            if row.close > row.ema_week * 1.00:
                if row.close > row.ema_month * 1.00:
                    if row.trend_15min < 0:
                        return self.execute_sell(row)

        last_trade = self.trader.get_last_trade()
        if last_trade:
            buy_price = last_trade.price
            if row.close < buy_price * self.bad_buy_limit:
                return self.execute_sell(row)       # High Loss - wrong buy

    def draw_line(self):
        plt.plot(self.market_data.index, self.market_data['ema_hour'], color='red')
        plt.plot(self.market_data.index, self.market_data['ema_day'], color='yellow')
        plt.plot(self.market_data.index, self.market_data['ema_12hours'], color='orange')
        plt.plot(self.market_data.index, self.market_data['ema_month'], color='yellow')

    def draw_color_line(self, ax, data_col_name, factor_col_name):
        # convert dates to numbers first
        inxval = mdates.date2num(self.market_data.index.to_pydatetime())
        points = np.array([inxval, self.market_data[data_col_name]]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        # colorize line
        # factor is from -1 -> 1
        cmap = ListedColormap(['r', 'b', 'g'])
        norm = BoundaryNorm([-200, -0.000002, 0.000002, 200], cmap.N)
        lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=1)
        lc.set_array(self.market_data[factor_col_name])
        ax.add_collection(lc)
        ax.plot(self.market_data.index, self.market_data[data_col_name], alpha=0.0)

    def draw_graph(self, from_symbol='BTC', to_symbol='BCH'):
        fig, ax = plt.subplots()
        fig.set_size_inches(10, 8)
        #ax.plot(self.market_data.index, self.market_data.close, color='gray')

        self.draw_line()
        self.draw_color_line(ax, 'close', 'color')

        #ax.plot(df.index, df['long_trend'], alpha=0.0)
        #ax.plot(df.index, df['long_trend'], color='orange')

        # SELL Signal
        below_threshold = self.market_data[self.market_data.signal == -1]
        plt.scatter(below_threshold.index, below_threshold['close'], color='red')

        # BUY Signal
        below_threshold = self.market_data[self.market_data.signal == 1]
        plt.scatter(below_threshold.index, below_threshold['close'], color='darkgreen')

        # helper lines
        # plt.plot(market_data.index, market_data['average'], color='gray')
        # plt.plot(df.index, df['ema100'], color='pink')

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        monthFmt = mdates.DateFormatter("%b")
        ax.xaxis.set_major_formatter(monthFmt)

        plt.title('market: {}'.format(self.market))
        plt.grid(True)

        xfmt = mdates.DateFormatter('%m-%d %H')
        ax.xaxis.set_major_formatter(xfmt)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))

        h = self.market_data.close.max() - self.market_data.close.min()
        y_min = self.market_data.close.min() - h / 2
        y_max = self.market_data.close.max() + h / 2
        plt.axis([self.market_data.index.min() + timedelta(hours=12),
                  self.market_data.index.max(), y_min, y_max])
        plt.setp(plt.gca().xaxis.get_majorticklabels(), 'rotation', 90)
        plt.show()

    def start_from(self, dt_from, days=30, from_symbol='BTC', plot=False):
        self.read_data(dt_from, days)
        print('read_data.. done ')
        self.bad_buy_limit = Decimal('0.97')
        self.calculate_signal(True)
        print(self.trader.balance)
        self.draw_graph()


if __name__ == "__main__":
    # dt_from = datetime.strptime('2017-08-30 9:40:00', '%Y-%m-%d %H:%M:%S')
    dt_from = datetime.utcnow()
    s = SimpleStrategy('BTC_ETH')
    s.start_from(dt_from, days=65)

    # dt_from = datetime.utcnow()
    # s = SimpleStrategy()
    # df = s.read_data(dt_from, days=10)
    # df['jDate'] = df.index.to_julian_date()
    #
    # fig, ax = plt.subplots()
    # fig.set_size_inches(10, 8)
    # ax.plot(df.index, df['close'], color='orange')
    #
    # ts_end = dt_from.timestamp()
    # start = datetime.fromtimestamp(ts_end - (86400 * 7))
    # end = datetime.fromtimestamp(ts_end - (86400 * 6))
    #
    # fig, ax = plt.subplots(figsize=(8, 6))
    # ax.plot(df.jDate, df.close)
    # a = get_trend(df, start, end, ax)
    # print(a)
    # plt.show()






