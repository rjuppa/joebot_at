import urllib
import json
import time
import hmac, hashlib
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime

import hashlib
import hmac
import json
import time
import sys

import requests
from configobj import ConfigObj
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from ratelimiter import RateLimiter

from pprint import pprint as pp


class API:
    # http
    public_url = "https://poloniex.com/public"
    private_url = "https://poloniex.com/tradingApi"
    topic = None
    limiter = None
    max_calls = 6
    max_period = 60
    secrets = None

    # wamp
    ws_uri = "wss://api.poloniex.com"
    ws_realm = "realm1"
    runner = None
    callback = None

    class RunningAPI(ApplicationSession):
        async def onJoin(self, details):
            await self.subscribe(self.callback, self.topic)

    def __init__(self, config: ConfigObj or dict() = {}):
        self.secrets = config
        self.limiter = RateLimiter(max_calls=self.max_calls, period=self.max_period)
        self.runner = ApplicationRunner(self.ws_uri, self.ws_realm)

    # WAMP Streaming API

    def subscribe(self, topic: str, callback: callable):
        self.callback = callback
        self.topic = topic
        self.runner.run(API.RunningAPI())

    # Public HTTP API, no credentials needed.

    def returnTicker(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def return24Volume(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnOrderBook(self, currencyPair: str = 'BTC_NXT', depth: int = 10):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnTradeHistory(self, currencyPair: str = 'BTC_NXT', start: int = 1410158341, end: int = 1410499372):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnChartData(self, currencyPair: str = 'BTC_NXT', start: int = 1405699200, end: int = 9999999999, period: int = 14400):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnCurrencies(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnLoanOrders(self, currency: str = 'BTC'):
        return self._call(sys._getframe().f_code.co_name, locals())

    # Private HTTP API Methods, Require API Key, and Secret on INIT

    def returnBalances(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnCompleteBalances(self, account: str = 'all'):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnDepositAddresses(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def generateNewAddress(self, currency: str = 'BTC'):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnDepositsWithdrawals(self, start: int = 1410158341, end: int = 1410499372):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnOpenOrders(self, currencyPair: str = 'BTC_XCP'):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnOrderTrades(self, orderNumber: int = None):
        return self._call(sys._getframe().f_code.co_name, locals())

    def buy(self, rate: float, amount: float, currencyPair: str, fillOrKill: int, immediateOrCancel: int, postOnly: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def sell(self, rate: float, amount: float, currencyPair: str, fillOrKill: int, immediateOrCancel: int, postOnly: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def cancelOrder(self, orderNumber: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def moveOrder(self, orderNumber: int, rate: float, amount: float, immediateOrCancel: int, postOnly: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def withdraw(self, currency: str, amount: float, address: str, paymentId: str):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnFeeInfo(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnAvailableAccountBalances(self, account: str = 'all'):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnTradableBalances(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def transferBalance(self, currency: str, amount: float, fromAccount: str, toAccount: str):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnMarginAccountSummary(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def marginBuy(self, currencyPair: str, rate: float, amount: float):
        return self._call(sys._getframe().f_code.co_name, locals())

    def marginSell(self, currencyPair: str, rate: float, amount: float):
        return self._call(sys._getframe().f_code.co_name, locals())

    def getMarginPosition(self, currencyPair: str):
        return self._call(sys._getframe().f_code.co_name, locals())

    def closeMarginPosition(self, currencyPair: str):
        return self._call(sys._getframe().f_code.co_name, locals())

    def createLoanOffer(self, currency: str, amount: float, duration: int, autoRenew: int, lendingRate: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def cancelLoanOffer(self, orderNumber: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def returnOpenLoanOffers(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnActiveLoans(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def returnLendingHistory(self):
        return self._call(sys._getframe().f_code.co_name, {})

    def toggleAutoRenew(self, orderNumber: int):
        return self._call(sys._getframe().f_code.co_name, locals())

    def _call(self, topic: str, args: dict() = {}):
        if topic in ['returnTicker', 'return24Volume', 'returnOrderBook', 'returnTradeHistory',
                     'returnChartData', 'returnCurrencies', 'returnLoanOrders']:
            api = [self.public_url, 'get', topic]
        else:
            api = [self.private_url, 'post', topic, self.secrets]

        def __call(api_details, uri):
            request = getattr(requests, api_details[1])
            headers = {}
            if 'self' in uri:
                del uri['self']
            uri['command'] = api_details[2]
            if api_details[1] == 'post':
                uri['nonce'] = int(time.time() * 1000)
                paybytes = urllib.parse.urlencode(uri).encode('utf8')
                sign = hmac.new(api_details[3]['secret'], paybytes, hashlib.sha512).hexdigest()
                headers['Sign'] = sign
                headers['Key'] = api_details[3]['api_key']
            return json.loads(request(api_details[0], uri, headers=headers).content.decode())

        with self.limiter:
            return __call(api, args)


def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))


class Poloniex2(object):
    def __init__(self):
        self.APIKey = ''
        self.Secret = ''

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if 'return' in after:
            if isinstance(after['return'], list):
                for x in range(0, len(after['return'])):
                    if isinstance(after['return'][x], dict):
                        if 'datetime' in after['return'][x] and 'timestamp' not in after['return'][x]:
                            after['return'][x]['timestamp'] = float(
                                createTimeStamp(after['return'][x]['datetime']))
        return after

    def api_query(self, command, req={}):

        if command == "returnTicker" or command == "return24Volume":
            ret = urlopen(urllib.request.Request('https://poloniex.com/public?command=' + command))
            return json.loads(ret.read())
        elif command == "returnOrderBook":
            ret = urlopen(urllib.request.Request(
                'https://poloniex.com/public?command=' + command + '&currencyPair=' + str(
                    req['currencyPair'])))
            return json.loads(ret.read())
        elif command == "returnMarketTradeHistory":
            ret = urlopen(urllib.request.Request(
                'https://poloniex.com/public?command=returnTradeHistory' + '&currencyPair=' + str(
                    req['currencyPair'])))
            return json.loads(ret.read())
        elif command == "returnChartData":
            ret = urlopen(urllib.request.Request(
                'https://poloniex.com/public?command=returnChartData' +
                '&currencyPair=' + str(req['currencyPair']) +
                '&start=' + str(req['start']) +
                '&end=' + str(req['end']) +
                '&period=' + str(req['period'])))
            return json.loads(ret.read())
        else:
            req['command'] = command
            req['nonce'] = int(time.time() * 1000)
            post_data = bytes(urlencode(req), encoding='UTF-8')

            sign = hmac.new(bytes(self.Secret, encoding='UTF-8'),
                            post_data,
                            hashlib.sha512).hexdigest()
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }

            ret = urlopen(
                urllib.request.Request('https://poloniex.com/tradingApi', post_data, headers))
            jsonRet = json.loads(ret.read())
            return self.post_process(jsonRet)

    def returnTicker(self):
        return self.api_query("returnTicker")

    def return24Volume(self):
        return self.api_query("return24Volume")

    def returnChartData(self):
        dt_from = datetime.utcnow()
        ts_now = dt_from.timestamp()
        currencyPair = 'BCH_BTC'
        start = ts_now - (864000*2)     # 10d
        end = ts_now
        period = 1800
        param = {'currencyPair': currencyPair,
                 'start': start,
                 'end': end,
                 'period': period
                 }
        return self.api_query('returnChartData', param)

    def returnOrderBook(self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})

    def returnMarketTradeHistory(self, currencyPair):
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair})

    # Returns all of your balances.
    # Outputs:
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def returnBalances(self):
        return self.api_query('returnBalances')

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def returnOpenOrders(self, currencyPair):
        return self.api_query('returnOpenOrders', {"currencyPair": currencyPair})

    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def returnTradeHistory(self, currencyPair):
        return self.api_query('returnTradeHistory', {"currencyPair": currencyPair})

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def buy(self, currencyPair, rate, amount):
        return self.api_query('buy', {"currencyPair": currencyPair, "rate": rate, "amount": amount})

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def sell(self, currencyPair, rate, amount):
        return self.api_query('sell',
                              {"currencyPair": currencyPair, "rate": rate, "amount": amount})

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs:
    # succes        1 or 0
    def cancel(self, currencyPair, orderNumber):
        return self.api_query('cancelOrder',
                              {"currencyPair": currencyPair, "orderNumber": orderNumber})

    # Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs:
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw',
                              {"currency": currency, "amount": amount, "address": address})
