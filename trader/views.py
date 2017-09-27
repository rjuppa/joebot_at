from django.shortcuts import render
from django.views.generic import DetailView, ListView
from datetime import datetime, timedelta

from trader.models import Trade
from ticker.strategies.simple import SimpleStrategy
import logging


class TradeList(ListView):
    logger = logging.getLogger(__name__)
    model = Trade
    queryset = Trade.objects.all()
    context_object_name = 'object_list'
    template_name = 'trader/trade/list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['btc_trader'] = self.btc_trader
        return super(TradeList, self).get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        dt_from = datetime.utcnow()
        s = SimpleStrategy('BTC_ETH')
        s.start_from(dt_from, days=30)
        self.btc_trader = s.trader
        return super(TradeList, self).get(request, *args, **kwargs)
