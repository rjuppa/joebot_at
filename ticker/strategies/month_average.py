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
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
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
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from ticker.strategies.base import BaseStrategy
from trader.btc_trader import BTCTrader



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


class MonthAverageStrategy(BaseStrategy):

    def read_data(self, dt_from, days=30):
        return super(MonthAverageStrategy, self).read_data(dt_from, days=days)

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

    def get_deep(self, row):
        return int(100 * row['close'] / row['ema_month']) - 100   # -100% .. 0 .. +100%

    def is_price_low(self, row):
        return row['close'] < row['ema_month_down']

    def is_price_high(self, row):
        return row['close'] > row['ema_month_up']

    def prepare_data(self):
        """
        Calculating all helper data columns
        Mostly based on exponential weighted mean and other rolling functions
        EMA and difference
        """
        self.market_data['jDate'] = self.market_data.index.to_julian_date()
        self.market_data['ema_hour'] = self.market_data['close'].ewm(span=12, adjust=False).mean()
        self.market_data['ema_hour_trend'] = self.market_data['ema_hour'].rolling(
            window=3, center=False).apply(func=lambda x: get_trend(x))

        self.market_data['ema_day'] = self.market_data['close'].ewm(
            span=self.prices_in_a_day, adjust=False).mean()

        self.market_data['ema_day_trend'] = self.market_data['ema_day'].rolling(
            window=3, center=False).apply(func=lambda x: get_trend(x))

        self.market_data['ema_week'] = self.market_data['close'].ewm(
            span=self.prices_in_a_day * 7, adjust=False).mean()

        self.market_data['ema_month'] = self.market_data['close'].ewm(
            span=self.prices_in_a_day * 30, adjust=False).mean()

        self.market_data['deep'] = self.market_data.apply(self.get_deep, axis=1)
        self.market_data['ema_month_down'] = self.market_data['ema_month'] * 0.90
        self.market_data['ema_month_up'] = self.market_data['ema_month'] * 1.05

        self.market_data['trend_1h'] = self.market_data['close'].rolling(
            window=12, center=False).apply(func=lambda x: get_trend(x))
        self.market_data['trend_30min'] = self.market_data['close'].rolling(
            window=6, center=False).apply(func=lambda x: get_trend(x))
        self.market_data['trend_15min'] = self.market_data['close'].rolling(
            window=3, center=False).apply(func=lambda x: get_trend(x))

        self.market_data['max_15min'] = self.market_data['close'].rolling(window=3).max()
        self.market_data['color'] = self.market_data.apply(self.get_color, axis=1)

    def get_signal_buy(self, row):
        """ Handle BUY conditions """
        ema_month_down = row.ema_month * 0.85   # luck 15% drop  STOP LOSS
        if row.close < ema_month_down:
            return self.execute_buy(row)

        ema_month_down = row.ema_month * 0.90
        if row.close < ema_month_down:
            if row.ema_hour_trend > 0 and row.max_15min > 0:
                return self.execute_buy(row)

    def get_signal_sell(self, row):
        """ Handle SELL conditions """
        ema_month_up = row.ema_month * 1.08     # luck 10% up    STOP LOSS
        if row.close > ema_month_up:
            return self.execute_sell(row)

        ema_month_up = row.ema_month * 1.05
        if row.close > ema_month_up:
            if row.trend_15min < 0:
                return self.execute_sell(row)

        if row.close < ema_month_up:
            if row.trend_15min < 0:
                if row.max_15min > ema_month_up:
                    return self.execute_sell(row)

    def draw_line(self):
        # plt.plot(self.market_data.index, self.market_data['ema_hour'], color='red')
        plt.plot(self.market_data.index, self.market_data['ema_day'], color='yellow')
        plt.plot(self.market_data.index, self.market_data['ema_month'], color='yellow')
        plt.plot(self.market_data.index, self.market_data['ema_month_down'], color='gray')
        plt.plot(self.market_data.index, self.market_data['ema_month_up'], color='gray')

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

        self.calculate_all_signals(True)
        print(self.trader.balance)
        self.draw_graph()

    def check_for_trading(self):
        dt_from = datetime.utcnow()
        self.read_data(dt_from)
        self.calculate_last_price_only()
        last_row = self.market_data.tail(1)
        if self.can_buy:  # have money
            last_row = self.market_data.tail(1)
            if self.is_price_low(last_row):
                # BUY
                if self.get_signal_buy(last_row):
                    self.notify('BUY', last_row)
                    return True

        if self.can_sell:  # have coins
            last_row = self.market_data.tail(1)
            if self.is_price_high(last_row):
                # SELL
                if self.get_signal_sell(last_row):
                    self.notify('SELL', last_row)
                    return True
        self.notify('NOTHING', last_row)
        return True


if __name__ == "__main__":
    # dt_from = datetime.strptime('2017-08-30 9:40:00', '%Y-%m-%d %H:%M:%S')
    dt_from = datetime.utcnow()
    s = MonthAverageStrategy('BTC_BCH')
    s.start_from(dt_from, days=65)
