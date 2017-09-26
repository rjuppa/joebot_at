# -*- coding: utf-8 -*-

# file with periodical tasks
from __future__ import absolute_import

from django.db.models import Q
from celery.utils.log import get_task_logger
from celery import shared_task
from decimal import Decimal
from joebot_at.taskapp.celery import app as celery_app
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabulate import tabulate
from poloniex import Poloniex
from .ots import OTS
from trader.models import Wallet
from trader.btc_trader import BTCTrader

logger = get_task_logger(__name__)

key = 'H028P3GK-FNBPQBWL-JY0SOOAH-DLMH997G'
secret = '33666a8181e087e0a7b7e6ed47225aeb9730ddc32e0b6f210ae4a1aaee0b812cfff929e48ce6e9ff2119722ddcec8279a24f616d2a10def20da6d74c43707764'

@shared_task
def test_task():
    print('Hello! It is {}'.format(datetime.utcnow()))
    return True


@shared_task
def get_ticker_task():
    exchange = Poloniex(key=key, secret=secret)
    data = exchange.returnTicker()
    print('Last price BTC_BCH: {}'.format(data['BTC_BCH']['last']))
    return True


@shared_task
def process_data_task():
    exchange = Poloniex()
    dt_from = datetime.utcnow()
    ts_now = dt_from.timestamp()
    time_from = ts_now - (864000)  # 10d
    data = exchange.returnChartData('BTC_BCH', period=300, start=time_from, end=ts_now)

    # print(data)
    processor = OTS()
    market_data = processor.load_data(data)


    # bad_buy_limit = processor.find_optimal_bad_buy_limit(market_data)
    # print('Optimal bad_buy_limit: {}% of buy price.'.format(bad_buy_limit))
    #
    # period = processor.find_optimal_rolling_window(market_data)
    # print('Optimal rolling_window: {}'.format(period))

    processor.calculate_signal(market_data, False)

    last_df = market_data.tail(1)
    print_df = last_df.drop(
        ['high', 'low', 'open', 'quoteVolume', 'weightedAverage', 'time', 'close_shift',
         'volume', 'close_shift2', 'add', 'average', 'mean20', 'ema_buy', 'ema5', 'diff2', 'diff',
         'ema100', 'balance'], axis=1)

    last_signal = market_data['signal'].iloc[-1]
    if last_signal > 0:
        # BUY BCH
        trader = BTCTrader('BTC_BCH')
        w = Wallet.objects.get(symbol='BTC')
        amount = w.balance()       # get balance
        trader.buy(last_df['close'], amount)

    if last_signal < 0:
        # SELL
        trader = BTCTrader('BTC_BCH')
        w = Wallet.objects.get(symbol='BCH')
        amount = w.balance()   # get balance
        trader.sell(last_df['close'], amount)

    print(tabulate(print_df, headers='keys', tablefmt='psql'))
    return True


@shared_task
def get_balance_task():
    polo = Poloniex(key=key, secret=secret)
    balance = polo.returnBalances()
    print('balance BTC: {}   BCH: {}'.format(balance['BTC'], balance['BCH']))
    return True
