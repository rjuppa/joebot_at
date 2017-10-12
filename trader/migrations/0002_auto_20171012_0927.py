# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-10-12 09:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='market',
            field=models.CharField(choices=[('BTC_BCH', 'BTC_BCH'), ('BTC_ETH', 'BTC_ETH'), ('BTC_LTC', 'BTC_LTC'), ('BTC_ZEC', 'BTC_ZEC'), ('BTC_XRP', 'BTC_XRP'), ('BTC_STR', 'BTC_STR'), ('BTC_XMR', 'BTC_XMR'), ('BTC_GNO', 'BTC_GNO'), ('BTC_STRAT', 'BTC_STRAT'), ('BTC_DASH', 'BTC_DASH')], help_text='Market', max_length=20),
        ),
    ]
