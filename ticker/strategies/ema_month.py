import json
import requests
import decimal
import numpy as np
import pandas as pd
from tabulate import tabulate
from decimal import Decimal

import os, sys
from os.path import dirname, realpath
proj_path = dirname(dirname(dirname(realpath(__file__))))

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
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from ticker.strategies.base import BaseStrategy


class EmaMonthStrategy(BaseStrategy):

    def read_data(self, dt_from, days=30):
        return super(EmaMonthStrategy, self).read_data(dt_from, days=days)

    def prepare_data(self):
        """
        Calculating all helper data columns
        Mostly based on exponential weighted mean and other rolling functions
        EMA and difference
        """
        self.market_data['jDate'] = self.market_data.index.to_julian_date()
        self.market_data['ema_month'] = self.market_data['close'].ewm(
            span=self.prices_in_a_day * 30, adjust=False).mean()

        self.market_data['ema_month_down'] = self.market_data['ema_month'] * 0.90
        self.market_data['ema_month_up'] = self.market_data['ema_month'] * 1.05

    def draw_line(self):
        plt.plot(self.market_data.index, self.market_data['close'], color='red')
        plt.plot(self.market_data.index, self.market_data['ema_month'], color='yellow')
        plt.plot(self.market_data.index, self.market_data['ema_month_down'], color='gray')
        plt.plot(self.market_data.index, self.market_data['ema_month_up'], color='gray')

    def draw_graph(self, from_symbol='BTC', to_symbol='BCH'):
        fig, ax = plt.subplots()
        fig.set_size_inches(10, 8)
        self.draw_line()

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
