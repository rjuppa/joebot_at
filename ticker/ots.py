import json
import requests
import decimal
import numpy as np
import pandas as pd
from tabulate import tabulate

import matplotlib
matplotlib.use('TkAgg')   # use for OSX

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from pandas.core.dtypes.common import PeriodDtype


def convert_ts(ts):
    return datetime.fromtimestamp(int(ts))          # .strftime('%Y-%m-%d %H:%M:%S')


class OTS(object):
    money = 0.0
    bitcoin = 0.0
    bitcoin_buy_price = 0.0
    bad_buy_limit = 0.90
    commission = 0.9975  # 0.25 %
    period = 50
    do_print = False

    def reset_money(self):
        self.money = 1000  # start money 5000USD
        self.bitcoin = 0.0

    def load_data(self, data):
        dates = [convert_ts(row['date']) for row in data]
        df = pd.DataFrame(data, index=dates,
                          columns=['date', 'high', 'low', 'open', 'close', 'volume', 'quoteVolume',
                                   'weightedAverage'])
        df['close'] = df['close'].astype(np.float64)
        df['time'] = df['date']
        return df

    def read_data(self, dt_from, count=2000, from_symbol='BTC', to_symbol='USD', exchange='Poloniex'):
        """ Load dataset from internet """
        ts_now = dt_from.timestamp()
        f = ts_now - (864000)     # 10d
        qs = 'fsym={}&tsym={}&toTs={}&e={}&limit={}'.format(from_symbol, to_symbol,
                                                            int(ts_now), exchange, count)
        if count <= 2000:
            url = 'https://min-api.cryptocompare.com/data/histohour?' + qs
        else:
            url = 'https://min-api.cryptocompare.com/data/histominute?' + qs

        url = 'https://poloniex.com/public?command=returnChartData&currencyPair=BTC_BCH&start={}&end={}&period=300'.format(f, ts_now)

        response = requests.get(url)
        data = json.loads(response.content)     #['Data']

        #df = pd.read_json(url, orient='records', convert_dates=True)
        #df.index = df['date']

        dates = [convert_ts(row['date']) for row in data]
        df = pd.DataFrame(data, index=dates, columns=['date', 'high', 'low', 'open', 'close', 'volume', 'quoteVolume', 'weightedAverage'])
        df[['high', 'low', 'open', 'close', 'volume', 'quoteVolume', 'weightedAverage']].apply(pd.to_numeric)
        df['time'] = df['date']
        # df.index = df['date'].map(lambda x: datetime.fromtimestamp(int(x)))
        df['balance'] = json.dumps({'usd': 0.0, 'btc': 0.0})
        plt.show()
        return df


    def get_balance(self, row):
        """ Executes a trade upon signal """
        if row.signal == 1:
            self.bitcoin = self.money / row.close
            self.money = 0.0
        if row.signal == -1:
            self.money = self.bitcoin * row.close
            self.bitcoin = 0.0
        return self.money + self.bitcoin * row.close

    def get_signal(self, row):
        """ Processes pre-signals and raise signals """
        # BUY
        if self.money > 0:  # have money
            if row.close < row.buy_line:
                # if price is low under EMA100

                if True:
                    # if buy_line goes up

                    if row.pre_signal == 1:
                        # trend is UP (pre_signal == 1)
                        self.bitcoin = self.money / row.close * self.commission
                        self.bitcoin_buy_price = row.close
                        self.money = 0
                        row.bank = self.money + self.bitcoin * row.close
                        if self.do_print:
                            print('{:%Y-%m-%d %H:%M}  ===  {:+d}   ---   {:8.3f}   ---  {:8.3f}   BUY:({:8.3f})'.format(
                                datetime.fromtimestamp(row.time),
                                int(row.pre_signal), self.money, self.bitcoin, row.close))
                        return 1
        # SELL
        if self.bitcoin > 0:
            if row.close > row.sell_line:
                if row.diff2 < 0:
                    self.money = self.bitcoin * row.close * self.commission
                    self.bitcoin = 0
                    if self.do_print:
                        print(
                            '{:%Y-%m-%d %H:%M}  ===  {:+d}   ---   {:8.3f}   ---  {:8.3f}   SELL({:8.3f})'.format(
                                datetime.fromtimestamp(row.time), int(row.pre_signal), self.money,
                                self.bitcoin, row.close))
                    return -1

            if row.close > row.ema100:
                # high price
                if row.pre_signal == -1:
                    # trend is DOWN (pre_signal == -1)
                    self.money = self.bitcoin * row.close * self.commission
                    self.bitcoin = 0
                    if self.do_print:
                        print('{:%Y-%m-%d %H:%M}  ===  {:+d}   ---   {:8.3f}   ---  {:8.3f}   SELL({:8.3f})'.format(
                            datetime.fromtimestamp(row.time), int(row.pre_signal), self.money, self.bitcoin, row.close))
                    return -1
            else:
                # low price
                if row.close < self.bitcoin_buy_price * self.bad_buy_limit:
                    # more then 10% loss - wrong buy
                    self.money = self.bitcoin * row.close * self.commission
                    self.bitcoin = 0.0
                    if self.do_print:
                        print('{:%Y-%m-%d %H:%M}  ===  {:+d}   ---   {:8.3f}   ---  {:8.3f}   SELL({:8.3f})'.format(
                            datetime.fromtimestamp(row.time), int(row.pre_signal), self.money, self.bitcoin, row.close))
                    return -1
        return 0

    def calculate_signal(self, df, is_print=False):
        """
        Calculating all helper data columns
        Mostly based on exponential weighted mean and other rolling functions
        EMA and difference
        """

        df['close_shift'] = df['close'].shift()
        df['close_shift2'] = df['close'].shift(2)

        df['ema100'] = df['close'].ewm(self.period).mean()
        df['average'] = df['ema100'].mean()
        df['ema5'] = df['close'].ewm(5).mean()
        df['ema_buy'] = df['close'].rolling(window=int(self.period / 2), center=True,
                                            min_periods=2).mean() * 0.98
        df['add'] = (df['ema5'] - df['average']) * 0.04     # if there is up hill add more
        df['buy_line'] = (df['ema100'] + df['ema_buy']) / 2 + df['add'].abs()
        df['sell_line'] = df['buy_line'] * 1.02

        df['ema5_diff'] = (df['ema5'].diff(periods=1) + df['ema5'].abs() / 100000)
        df['mean20'] = df['close'].rolling(window=int(self.period / 4), center=True,
                                           min_periods=2).mean()

        df['diff2'] = (df['ema5'].diff(periods=1) + df['ema5'] / 100000)  # this is tolerance when derivation is near zero
        df['diff'] = df['diff2'].rolling(window=int(self.period / 4), center=True, min_periods=1).mean()

        df['color'] = np.where(df['diff'] < 0, -2, np.where(df['diff'] > 0, 2, 0))
        df['color_shift'] = np.where(df['diff'].shift() < 0, -2,
                                     np.where(df['diff'].shift() > 0, 2, 0))
        df['color_shift2'] = np.where(df['diff'].shift(2) < 0, -2,
                                      np.where(df['diff'].shift(2) > 0, 2, 0))
        df['color_shift3'] = np.where(df['diff'].shift(3) < 0, -2,
                                      np.where(df['diff'].shift(3) > 0, 2, 0))
        df['pre_signal'] = df.apply(self.get_presignal, axis=1)

        if is_print:
            print('Starts with:')
            print('Money = 5000 USD')
            print('Coins = 0 BTC')
            print('DateTime          ===  S    ---        USD   ---      Coin    Price in USD')
            self.do_print = True

        df['signal'] = df.apply(self.get_signal, axis=1)

        self.reset_money()
        df['balance'] = df.apply(self.get_balance, axis=1)
        return df

    def draw_graph(self, df, from_symbol='BTC', to_symbol='BCH'):
        fig, ax = plt.subplots()
        fig.set_size_inches(10, 8)
        ax.plot(df.index, df['close'], alpha=0.0)

        # convert dates to numbers first
        inxval = mdates.date2num(df.index.to_pydatetime())
        points = np.array([inxval, df['close']]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        # colorize line
        cmap = ListedColormap(['r', 'b', 'g'])
        norm = BoundaryNorm([-2, -1, 1, 2], cmap.N)
        lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=1)
        lc.set_array(df['color'])
        ax.add_collection(lc)

        # SELL Signal
        below_threshold = df[df['signal'] == -1]
        plt.scatter(below_threshold.index, below_threshold['close'], color='red')

        # BUY Signal
        below_threshold = df[df['signal'] == 1]
        plt.scatter(below_threshold.index, below_threshold['close'], color='darkgreen')

        # helper lines
        # plt.plot(market_data.index, market_data['average'], color='gray')
        # plt.plot(df.index, df['ema100'], color='pink')
        plt.plot(df.index, df['buy_line'], color='orange')
        plt.plot(df.index, df['sell_line'], color='orange')
        plt.plot(df.index, df['ema5'], color='black')


        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        monthFmt = mdates.DateFormatter("%b")
        ax.xaxis.set_major_formatter(monthFmt)

        plt.title('{}/{}'.format(from_symbol, to_symbol))
        plt.grid(True)

        xfmt = mdates.DateFormatter('%m-%d %H')
        ax.xaxis.set_major_formatter(xfmt)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))

        h = df['close'].max() - df['close'].min()
        y_min = df['close'].min() - h / 2
        y_max = df['close'].max() + h / 2
        plt.axis([df.index.min() + timedelta(hours=12), df.index.max(), y_min, y_max])
        plt.setp(plt.gca().xaxis.get_majorticklabels(), 'rotation', 90)
        plt.show()

    def find_optimal_bad_buy_limit(self, df, plot=False):
        bad_buy_limit_data = []
        bad_buy_limit_profit = []
        market_data_copy = df.copy(True)
        for limit in np.arange(0.99, 0.75, -0.01):
            self.bad_buy_limit = limit
            market_data = self.calculate_signal(market_data_copy)
            bad_buy_limit_data.append(self.bad_buy_limit)
            bad_buy_limit_profit.append(int(market_data.tail(1)['balance']))
            self.reset_money()

        bad_buy_limit_df = pd.DataFrame(
            {'bad_buy_limit': bad_buy_limit_data,
             'profit': bad_buy_limit_profit})

        if plot:
            bad_buy_limit_df.plot(x='bad_buy_limit', y='profit')
            plt.title('BAD BUY LIMIT %')
            plt.grid(True)
        return bad_buy_limit_df.ix[bad_buy_limit_df['profit'].idxmax()]['bad_buy_limit']

    def find_optimal_rolling_window(self, df, plot=False):
        rolling_window_data = []
        rolling_window_profit = []
        market_data_copy = df.copy(True)
        for rolling_window in np.arange(12, 120, 1):
            self.period = rolling_window
            market_data = self.calculate_signal(market_data_copy)
            rolling_window_data.append(self.period)
            rolling_window_profit.append(int(market_data.tail(1)['balance']))
            self.reset_money()

        rolling_window_df = pd.DataFrame(
            {'rolling_window': rolling_window_data,
             'profit': rolling_window_profit})

        if plot:
            rolling_window_df.plot(x='rolling_window', y='profit')
            plt.title('ROLLING WINDOW SIZE')
            plt.grid(True)
        return rolling_window_df.ix[rolling_window_df['profit'].idxmax()]['rolling_window']

    def start_from(self, dt_from, from_symbol='BTC', plot=False):
        from_symbol = 'BTC'
        to_symbol = 'BCH'
        market_data = self.read_data(dt_from, 2000, from_symbol=from_symbol, to_symbol=to_symbol)
        print('read_data.. done ')

        # print('Calculating optimal BAD BUY limit..')
        # self.bad_buy_limit = self.find_optimal_bad_buy_limit(market_data, plot)
        # print('Optimal bad_buy_limit: {}% of buy price.'.format(self.bad_buy_limit))
        #
        # print('Calculating optimal rolling window size..')
        # self.period = self.find_optimal_rolling_window(market_data, plot)
        # print('Optimal rolling_window: {}'.format(self.period))

        self.bad_buy_limit = 0.97
        self.period = 70
        self.reset_money()

        market_data = self.calculate_signal(market_data, True)
        self.draw_graph(market_data)

if __name__ == "__main__":
    # dt_from = datetime.strptime('2017-08-30 9:40:00', '%Y-%m-%d %H:%M:%S')
    dt_from = datetime.utcnow()
    ots = OTS()
    ots.start_from(dt_from)
