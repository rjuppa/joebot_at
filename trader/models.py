from django.db import models
from django.db.models import Sum
from django.utils.encoding import python_2_unicode_compatible

from decimal import Decimal

# Create your models here.


BUY = 'BUY'
SELL = 'SELL'
TRADE_TYPES = (
    (BUY, 'BUY'),
    (SELL, 'SELL'),
)

MARKETS = [('BTC_BCH', 'BTC_BCH'),
           ('BTC_ETH', 'BTC_ETH'),
           ('BTC_LTC', 'BTC_LTC'),
           ('BTC_ZEC', 'BTC_ZEC'),
           ('BTC_XRP', 'BTC_XRP'),
           ('BTC_STR', 'BTC_STR'),
           ('BTC_XMR', 'BTC_XMR'),
           ('BTC_GNO', 'BTC_GNO'),
           ('BTC_STRAT', 'BTC_STRAT'),
           ('BTC_DASH', 'BTC_DASH'),]


def get_coin_labels():
    labels = ['BTC']
    for m in MARKETS:
        labels.append(str(m[0])[4:])
    return labels


@python_2_unicode_compatible
class Exchange(models.Model):
    name = models.CharField(
        max_length=100,
    )
    slug = models.CharField(
        max_length=100,
    )
    fee = models.DecimalField(max_digits=7, decimal_places=5,  default=0.25)

    class Meta:
        app_label = 'trader'
        verbose_name = 'Exchange'

    def __str__(self):
        return "{}".format(self.name)

    @property
    def fee_argument(self):
        return (Decimal(100.00) - Decimal(self.fee)) / Decimal(100.00)


@python_2_unicode_compatible
class Wallet(models.Model):

    # ADD Exchange TODO
    symbol = models.CharField(
        max_length=100,
    )
    name = models.CharField(
        max_length=100,
    )

    class Meta:
        app_label = 'trader'
        verbose_name = 'Wallet'

    @classmethod
    def get_or_create(cls, symb):
        try:
            obj = Wallet.objects.get(symbol=symb)
        except Wallet.DoesNotExist:
            obj = Wallet(symbol=symb, name=symb)
            obj.save()
        return obj

    def __str__(self):
        return "{}".format(self.symbol)

    # initial 0.2 BTC
    # ########################### BUY  1.0 ETH - pay 0.123 BTC
    # price: 0.123 BTC
    # amount_buy: 0.9997 ETH
    # amount_sell: -0.123 BTC
    # amount_usd: 330 USD
    # fee: 0.0003 BTC

    # ########################### SELL 1.0 ETH - pay 0.131 BTC
    # price: 0.131 BTC
    # amount_buy: -0.9997 ETH
    # amount_sell: 0.130 BTC
    # amount_usd: 342 USD
    # fee: 0.0003 BTC

    # balance: 0.2 -0.123  +0.130 = 0.207
    def balance_from(self):
        dic_sell = self.trades_from.filter(type=SELL, market__startswith=self.symbol).aggregate(Sum('amount_sell'))  # BTC
        dic_buy = self.trades_to.filter(type=BUY, market__startswith=self.symbol).aggregate(Sum('amount_sell'))
        amount_sell = dic_sell['amount_sell__sum'] if dic_sell and dic_sell['amount_sell__sum'] else Decimal('0.0')
        amount_buy = dic_buy['amount_sell__sum'] if dic_buy and dic_buy['amount_sell__sum'] else Decimal('0.0')
        return Decimal(amount_sell) + Decimal(amount_buy)

    def balance_to(self):
        dic_sell = self.trades_from.filter(type=SELL, market__endswith=self.symbol).aggregate(Sum('amount_buy'))  # BTC
        dic_buy = self.trades_to.filter(type=BUY, market__endswith=self.symbol).aggregate(Sum('amount_buy'))
        amount_sell = dic_sell['amount_buy__sum'] if dic_sell and dic_sell['amount_buy__sum'] else Decimal('0.0')
        amount_buy = dic_buy['amount_buy__sum'] if dic_buy and dic_buy['amount_buy__sum'] else Decimal('0.0')
        return Decimal(amount_sell) + Decimal(amount_buy)


@python_2_unicode_compatible
class Trade(models.Model):

    exchange = models.ForeignKey(
            'trader.Exchange',
            on_delete=models.CASCADE,
        )
    market = models.CharField(
        choices=MARKETS,
        max_length=20,
        help_text='Market',
    )
    type = models.CharField(
        choices=TRADE_TYPES,
        max_length=20,
        help_text='Trade Type',
    )
    wallet_from = models.ForeignKey(        # usually BTC
        'trader.Wallet',
        on_delete=models.CASCADE,
        related_name='trades_from',
    )

    wallet_to = models.ForeignKey(
        'trader.Wallet',
        on_delete=models.CASCADE,
        related_name='trades_to',
    )

    # ########################### BUY  1.0 ETH - pay 0.123 BTC
    # price: 0.123 BTC
    # amount_buy: 0.9997 ETH
    # amount_sell: -0.123 BTC
    # amount_usd: 330 USD
    # fee: 0.0003 BTC

    # ########################### SELL 1.0 ETH - pay 0.131 BTC
    # price: 0.131 BTC
    # amount_buy: -0.9997 ETH
    # amount_sell: 0.130 BTC
    # amount_usd: 342 USD
    # fee: 0.0003 BTC

    price = models.DecimalField(max_digits=19, decimal_places=10)           # 0.123 BTC for 1ETH - BUY
    amount_buy = models.DecimalField(max_digits=19, decimal_places=10)      # 1 ETH
    amount_sell = models.DecimalField(max_digits=19, decimal_places=10)     # 0.123 BTC
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)       # 330 USD
    fee = models.DecimalField(max_digits=19, decimal_places=10)             # 0.0003 BTC (0.95 USD)

    is_success = models.BooleanField(
        blank=True,
        default=False,
    )

    trader = models.CharField(
        max_length=100,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        app_label = 'trader'
        verbose_name = 'Trade'

    def __str__(self):
        return "{} {} {}".format(self.created_at.strftime('%Y-%m-%d %H:%M'),
                                 self.market, self.type, self.price)

    @property
    def is_buy(self):
        return self.type == BUY

    @property
    def is_sell(self):
        return self.type == SELL

