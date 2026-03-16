# core/utils/celery_helpers.py

from django.conf import settings

def run_task(task, *args, **kwargs):
    """
    Run a Celery task either asynchronously (if worker exists)
    or synchronously (useful for free tier without workers).
    """
    if getattr(settings, "FREE_TIER", False):
        # Run synchronously
        return task.run(*args, **kwargs)
    else:
        # Run asynchronously with Celery worker
        return task.delay(*args, **kwargs)