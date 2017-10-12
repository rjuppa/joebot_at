from .models import *
from chatbot.models import Message
from chatbot.bot import MessageBot

ZERO = Decimal('0.0')


class BTCTrader(object):

    def __init__(self, market):
        self.sym_from, self.sym_to = market.split('_')
        if self.sym_from in [m[0] for m in MARKETS]:
            raise ValueError('Unsupported market: sym_from.')
        if self.sym_to in [m[0] for m in MARKETS]:
            raise ValueError('Unsupported market: sym_to.')

        self.exchange = Exchange.objects.get(slug='poloniex')
        self.market = market

        self.wallet_from = Wallet.get_or_create(self.sym_from)
        self.wallet_to = Wallet.get_or_create(self.sym_to)

    def clear_market(self, deposit_btc=0):
        Trade.objects.filter(exchange=self.exchange, market=self.market).delete()
        if deposit_btc > 0:
            self.deposit_btc(deposit_btc)

    def get_last_trade(self):
        trade = Trade.objects.filter(exchange=self.exchange, market=self.market).last()
        return trade if trade and trade.price > 0 else None

    def deposit_btc(self, amount):
        trade = Trade(exchange=self.exchange, market=self.market, type=SELL)
        trade.wallet_from = self.wallet_from    # BTC
        trade.wallet_to = self.wallet_to
        trade.price = 0
        trade.amount_buy = 0  # BCH
        trade.amount_sell = amount
        trade.fee = 0
        trade.amount_usd = amount * 4000
        trade.save()

    def withdrawal_btc(self, amount):
        trade = Trade(exchange=self.exchange, market=self.market, type=BUY)
        trade.wallet_from = self.wallet_from    # BTC
        trade.wallet_to = self.wallet_to
        trade.price = 0
        trade.amount_buy = 0  # BCH
        trade.amount_sell = -amount
        trade.fee = 0
        trade.amount_usd = amount * 4000
        trade.save()

    def deposit_coin(self, amount, price=0):
        trade = Trade(exchange=self.exchange, market=self.market, type=BUY)
        trade.wallet_from = self.wallet_from    # BTC
        trade.wallet_to = self.wallet_to
        trade.price = price
        trade.amount_buy = amount
        trade.amount_sell = 0
        trade.fee = 0
        trade.amount_usd = amount * price * 4000
        trade.save()

    def withdrawal_coin(self, amount, price=0):
        trade = Trade(exchange=self.exchange, market=self.market, type=SELL)
        trade.wallet_from = self.wallet_from    # BTC
        trade.wallet_to = self.wallet_to
        trade.price = price
        trade.amount_buy = -amount
        trade.amount_sell = 0
        trade.fee = 0
        trade.amount_usd = amount * price * 4000
        trade.save()

    def buy(self, price, amount):
        if isinstance(price, (float,)):
            price = Decimal(str(price))
        if isinstance(amount, (float,)):
            amount = Decimal(str(amount))
        trade = Trade(exchange=self.exchange, market=self.market, type=BUY)
        trade.wallet_from = self.wallet_from
        trade.wallet_to = self.wallet_to
        trade.price = price
        trade.amount_buy = amount * self.exchange.fee_argument          # Coin
        trade.amount_sell = -(price * amount)                           # BTC
        trade.fee = price * amount * self.exchange.fee
        trade.amount_usd = trade.amount_sell * 4000
        trade.save()
        text = self.market + ' Executed BUY@{}'
        self.send_telegram(text, price)

    def sell(self, price, amount):
        if isinstance(price, (float,)):
            price = Decimal(str(price))
        if isinstance(amount, (float,)):
            amount = Decimal(str(amount))
        trade = Trade(exchange=self.exchange, market=self.market, type=SELL)
        trade.wallet_from = self.wallet_from
        trade.wallet_to = self.wallet_to
        trade.price = price
        trade.amount_buy = -amount                                                # Coin
        trade.amount_sell = price * amount * self.exchange.fee_argument           # BTC
        trade.fee = price * amount * self.exchange.fee
        trade.amount_usd = trade.amount_sell * 4000
        trade.save()
        text = self.market + ' Executed SELL@{}'
        self.send_telegram(text, price)

    def get_balance_btc(self):
        qs = Trade.objects.filter(market__startswith=self.sym_from)
        _sell = qs.filter(type=SELL).aggregate(Sum('amount_sell'))  # BTC
        amount_sell = _sell['amount_sell__sum'] if _sell and _sell['amount_sell__sum'] else ZERO

        _buy = qs.filter(type=BUY).aggregate(Sum('amount_sell'))
        amount_buy = _buy['amount_sell__sum'] if _buy and _buy['amount_sell__sum'] else ZERO
        return Decimal(amount_sell) + Decimal(amount_buy)

    def get_balance_coin(self):
        qs = Trade.objects.filter(market__endswith=self.sym_to)
        _sell = qs.filter(type=SELL).aggregate(Sum('amount_buy'))  # Coin
        amount_sell = _sell['amount_buy__sum'] if _sell and _sell['amount_buy__sum'] else ZERO

        _buy = qs.filter(type=BUY).aggregate(Sum('amount_buy'))
        amount_buy = _buy['amount_buy__sum'] if _buy and _buy['amount_buy__sum'] else ZERO
        return Decimal(amount_sell) + Decimal(amount_buy)

    def how_many_coins_for_btc(self, price, amount_btc):
        return amount_btc * self.exchange.fee_argument / price

    @property
    def balance(self):
        return '{} {}  ({} {})'.format(self.get_balance_btc(), self.sym_from,
                                       self.get_balance_coin(), self.sym_to,)

    def get_last_message(self):
        return Message.objects.filter(market=self.market).last()

    def send_telegram(self, text, price):
        last = self.get_last_message()
        if text != last:
            bot = MessageBot()
            bot.send_message_to_me(text.format(price))
            msg = Message(market=self.market, text=text, price=price, incoming=False)
            msg.save()
