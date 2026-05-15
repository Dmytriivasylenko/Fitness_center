from celery import Celery

celery = Celery(
    'app',
    broker='amqp://guest:guest@rabbitmq:5672//',
    backend='rpc://'
)

celery.autodiscover_tasks(['app'], force=True)
