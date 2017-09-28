import os
import requests
import numpy as np
import pandas as pd
from tabulate import tabulate
from decimal import Decimal

import matplotlib
matplotlib.use('TkAgg')   # use for OSX

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from pandas.core.dtypes.common import PeriodDtype

from trader.btc_trader import BTCTrader
from pprint import pprint as pp


def convert_ts(ts):
    return datetime.fromtimestamp(int(ts))          # .strftime('%Y-%m-%d %H:%M:%S')


class BaseStrategy(object):
    bad_buy_limit = 0.90
    commission = 0.9975  # 0.25 %
    prices_in_a_day = 288
    sec_in_a_price = 300
    do_print = False
    url = 'https://poloniex.com/public?command=returnChartData'
    market = 'BTC_BCH'
    market_data = None
    ts_current = 0
    ts_start = 0
    trader = None
    trade_amount_btc = Decimal('0.2')  # 0.2BTC
    trade_min_amount_btc = Decimal('0.02')  # 0.02BTC
    available_btc = Decimal('0.0')
    available_coin = Decimal('0.0')
    dir_log = 'logs'

    def __init__(self, market):
        self.market = market
        self.trader = BTCTrader(market)
        self.trader.clear_market(deposit_btc=0.2)

        # check if dir. logs/ exists
        if not os.path.exists(self.dir_log):
            os.makedirs(self.dir_log)

    def load_data(self, data):
        dates = [convert_ts(row['date']) for row in data]
        self.market_data = pd.DataFrame(data, index=dates, columns=['date', 'high', 'low',
                                                                    'open', 'close', 'volume',
                                                                    'quoteVolume', 'weightedAverage'])
        self.market_data['close'] = self.market_data['close'].astype(np.float64)  # force type float64
        return self.market_data

    def read_data(self, dt_from, days=1):
        """ Load dataset from internet """
        self.ts_current = int(dt_from.timestamp())
        self.ts_start = self.ts_current - (self.prices_in_a_day * self.sec_in_a_price * days)
        # read data aggregated by 5min
        url = '{}&currencyPair={}&start={}&end={}&period=300'.format(self.url,
                                                                     self.market,
                                                                     self.ts_start, self.ts_current)
        response = requests.get(url)
        data = response.json()  # data
        if not isinstance(data, list):
            print(url)
            print('Http Status:{} - {}'.format(response.status_code, response.content[:80]))
            raise Exception('HTTP ERROR')

        dates = [convert_ts(row['date']) for row in data]   # index
        cc = pd.DataFrame(data, index=dates, columns=['date', 'high', 'low', 'open',
                                                      'close', 'volume', 'quoteVolume',
                                                      'weightedAverage'])
        cc[['high', 'low', 'open', 'close', 'volume', 'quoteVolume', 'weightedAverage']].apply(pd.to_numeric)
        cc['close'] = cc['close'].astype(np.float64)  # force type float64
        self.market_data = cc[['close', 'date']].copy()
        return self.market_data

    def prepare_data(self):
        """ To Override - Calculating all helper data columns"""
        pass

    def calculate_all_signals(self, is_print=False):
        """
        Calculating all helper data columns
        Mostly based on exponential weighted mean and other rolling functions
        EMA and difference
        """
        self.prepare_data()
        if is_print:
            self._print_header()
            self.do_print = True

        self.market_data['signal'] = self.market_data.apply(self.get_signal, axis=1)
        return self.market_data

    def calculate_last_price_only(self):
        self.prepare_data()

    def execute_buy(self, row):
        price = Decimal(str(row.close))
        self.available_btc = self.trader.get_balance_btc()
        if self.available_btc > self.trade_amount_btc:
            amount_btc = self.available_btc #self.trade_amount_btc
        else:
            amount_btc = self.available_btc

        if amount_btc > self.trade_min_amount_btc:
            # buy if have btc
            amount = amount_btc / price
            self.trader.buy(price, amount)
            self.available_btc = self.trader.get_balance_btc()
            self.available_coin = self.trader.get_balance_coin()
            if self.do_print:
                self._print_trade(row)
            return 1
        return 0

    def execute_sell(self, row):
        price = Decimal(str(row.close))
        self.available_coin = self.trader.get_balance_coin()
        if (self.available_coin * price) > self.trade_amount_btc:
            amount = self.available_coin #self.trade_amount_btc / price
        else:
            amount = self.available_coin

        if amount * price > self.trade_min_amount_btc:
            # sell if have coins
            self.trader.sell(price, amount)
            self.available_btc = self.trader.get_balance_btc()
            self.available_coin = self.trader.get_balance_coin()
            if self.do_print:
                self._print_trade(row)
            return -1
        return 0

    def get_signal_buy(self, row):
        """ Handle BUY conditions """
        return 0    # TODO

    def get_signal_sell(self, row):
        """ Handle SELL conditions """
        return 0     # TODO

    @property
    def can_buy(self):
        return self.available_btc > 0   # we have btc

    @property
    def can_sell(self):
        return self.available_coin > 0  # we have coins

    def get_signal(self, row):
        """ Processes signal for a row """
        self.available_btc = self.trader.get_balance_btc()
        self.available_coin = self.trader.get_balance_coin()
        # BUY
        if self.can_buy:
            return self.get_signal_buy(row)

        # SELL
        if self.can_sell:
            return self.get_signal_sell(row)

        return 0

    def notify(self, type, row):
        price = '{:4.8f}'.format(row['close'].values[0])
        deep = row['deep'].values[0]
        date = datetime.fromtimestamp(int(row['date'].values[0])).strftime('%Y-%m-%d %H:%M:%S')
        if type == 'NOTHING':
            self.write_log('{}|{}|{} |{}%'.format(date, self.trader.market, price, deep))
        else:
            status = '{} {}'.format(self.available_coin, self.available_coin)
            self.write_log('{}|{}|{} - {} SIGNAL - STATUS: {}'.format(date, self.trader.market,
                                                                      price, type, status))

    def write_log(self, line):
        path = '{}/{}.txt'.format(self.dir_log, self.market)
        mode = 'a' if os.path.exists(path) else 'w'
        hs = open(path, mode)
        hs.write(line + '\n')
        hs.close()

    def draw_line(self):
            pass

    def draw_graph(self, from_symbol='BTC', to_symbol='BCH'):
        fig, ax = plt.subplots()
        fig.set_size_inches(10, 8)
        ax.plot(self.market_data.index, self.market_data.close, alpha=0.0)

        # convert dates to numbers first
        inxval = mdates.date2num(self.market_data.index.to_pydatetime())
        points = np.array([inxval, self.market_data.close]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        # colorize line
        cmap = ListedColormap(['r', 'b', 'g'])
        norm = BoundaryNorm([-2, -1, 1, 2], cmap.N)
        lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=1)
        lc.set_array(self.market_data.color)
        ax.add_collection(lc)

        # helper lines
        self.draw_line()

        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        monthFmt = mdates.DateFormatter("%b")
        ax.xaxis.set_major_formatter(monthFmt)

        plt.title('{}/{}'.format(from_symbol, to_symbol))
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

    def _print_header(self):
        print('Starts with: {}'.format(self.trader.balance))
        print('DateTime          ===       BTC   ---      Coin      Price')

    def _print_trade(self, row):
        print('{:%Y-%m-%d %H:%M}  ===    {:8.3f}   ---  {:8.3f}   ({:8.3f})'.format(
            datetime.fromtimestamp(row.date),
            self.available_btc,
            self.available_coin,
            row.close))

    def start_from(self, dt_from, days=30):
        self.read_data(dt_from, days)
        print('read_data.. done ')
        self.bad_buy_limit = 0.97
        self.calculate_all_signals(True)
        self.draw_graph()


if __name__ == "__main__":
    # dt_from = datetime.strptime('2017-08-30 9:40:00', '%Y-%m-%d %H:%M:%S')
    dt_from = datetime.utcnow()
    s = BaseStrategy('BTC_ETH')
    s.start_from(dt_from)
