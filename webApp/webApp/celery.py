from __future__ import absolute_import
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webApp.settings')

from django.conf import settings
from celery import Celery

app = Celery('webApp',
				backend ='amqp',
				broker = 'amqp://guest@localhost//'
			)

app.config_from_object('django.conf:settings')

app.autodiscover_tasks('django.conf:settings')

@app.task(bind=True)
def debug_task(self):
	print("Request: {0!r}".format(self.request))