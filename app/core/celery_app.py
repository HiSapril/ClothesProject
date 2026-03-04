from celery import Celery
from celery.signals import setup_logging, task_prerun, task_postrun
from app.core.config import settings
from app.core.logging_config import setup_logging as app_setup_logging, task_id_ctx, request_id_ctx
import logging

# Initialize Celery
celery_app = Celery(
    "outfit_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.task_routes = {
    "process_clothing_ai": {"queue": "default"}
}

# --- Celery Logging Strategy ---

@setup_logging.connect
def config_loggers(*args, **kwtags):
    # Use our app's structured logging config for Celery workers
    app_setup_logging()

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    # Set task_id in context
    task_id_ctx.set(task_id)
    
    # Extract request_id from task arguments (if passed)
    # By convention, we'll pass 'request_id' as a keyword argument
    rid = kwargs.get("request_id")
    if rid:
        request_id_ctx.set(rid)
    
    logger = logging.getLogger("app")
    logger.info(f"Task {task.name} started")

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    logger = logging.getLogger("app")
    logger.info(f"Task {task.name} completed with status: {kwargs.get('state')}")
    
    # Clear contextvars
    task_id_ctx.set(None)
    request_id_ctx.set(None)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=30, # seconds
    task_time_limit=45,      # seconds (hard)
)
