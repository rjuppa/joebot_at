
import os
from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings


if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover


app = Celery('joebot_at')


class CeleryConfig(AppConfig):
    name = 'joebot_at.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        print('------------------ CELERY CONFIG LOADED -----------------')
        app.config_from_object('django.conf:settings', namespace='CELERY', force=True)
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)
        app.conf.update(
            beat_scheduler='django_celery_beat.schedulers.DatabaseScheduler',
        )

        print('beat_scheduler: {}'.format(app.conf['beat_scheduler']))
        print('broker_url: {}'.format(app.conf['broker_url']))


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover
