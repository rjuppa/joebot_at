# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from ticker.tasks import get_ticker_task


class Command(BaseCommand):
    """ Run Celery task """

    def handle(self, *args, **options):
        get_ticker_task.delay()
