from celery import Celery

app = Celery(
    "solpic_worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="rpc://"
)
app.autodiscover_tasks(["tasks.analyze_pipeline"])
