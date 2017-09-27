# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from ticker.tasks import process_month_avg_task


class Command(BaseCommand):
    """ Run Celery task """

    def handle(self, *args, **options):
        process_month_avg_task.delay()
