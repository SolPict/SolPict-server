from celery import Celery

celery_app = Celery(
    "solpic_api",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="rpc://",
)
