import os

from celery import Celery
from celery.schedules import crontab

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("tasks", backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)

celery_app.conf.timezone = "US/Pacific"

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
)

# Scheduling tips: (https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
# crontab() ==> Execute every minute.
# crontab(minute=0, hour=0) ==> Execute daily at midnight.
# crontab(minute=0, hour='*/3') ==> Execute every three hours: midnight, 3am, 6am, 9am, noon, 3pm, 6pm, 9pm.
# crontab(minute=0, hour='0,3,6,9,12,15,18,21') ==> Same as previous.
# crontab(minute='*/15') ==> Execute every 15 minutes.
# crontab(day_of_week='sunday') ==> Execute every minute on Sundays.
# crontab(minute='*', hour='*', day_of_week='sun') ==> Same as previous.
# crontab(minute='*/10', hour='3,17,22', day_of_week='thu,fri') ==> Execute every ten minutes, but only between 3-4 am, 5-6 pm, and 10-11 pm on Thursdays or Fridays.
# crontab(minute=0, hour='*/2,*/3') ==> Execute every even hour, and every hour divisible by three. This means: at every hour except: 1am, 5am, 7am, 11am, 1pm, 5pm, 7pm, 11pm
# crontab(minute=0, hour='*/5') ==> Execute hour divisible by 5. This means that it is triggered at 3pm, not 5pm (since 3pm equals the 24-hour clock value of “15”, which is divisible by 5).
# crontab(minute=0, hour='*/3,8-17') ==> Execute every hour divisible by 3, and every hour during office hours (8am-5pm).
# crontab(0, 0, day_of_month='2') ==> Execute on the second day of every month.
# crontab(0, 0, day_of_month='2-30/2') ==> Execute on every even numbered day.
# crontab(0, 0, day_of_month='1-7,15-21') ==> Execute on the first and third weeks of the month.
# crontab(0, 0, day_of_month='11', month_of_year='5') ==> Execute on the eleventh of May every year.
# crontab(0, 0, month_of_year='*/3') ==> Execute every day on the first month of every quarter.


celery_app.conf.beat_schedule = {
    ## this task is for demonstration purposes.
    # "add-every-3-mins": {
    #     "task": "lyra.bg_worker.add",
    #     "schedule": 3 * 60,
    #     "args": (16, 16),
    # },
    "update-static-references": {
        "task": "lyra.bg_worker.background_build_static_references",
        # daily at midnight
        "schedule": crontab(minute=0, hour=0),
    },
    "update-drooltool-database": {
        "task": "lyra.bg_worker.background_update_drooltool_database",
        # daily at midnight
        "schedule": crontab(minute=0, hour=0),
        # on the 10th of each month
        # "schedule": crontab( minute=0, hour=0, day_of_month=10),
    },
    "update-drooltool-rsb_geo": {
        "task": "lyra.bg_worker.background_update_rsb_geojson",
        # daily at midnight
        "schedule": crontab(minute=0, hour=0),
        # on the 10th of each month
        # "schedule": crontab(minute=0, hour=0, day_of_month=10),
    },
}
celery_app.conf.timezone = "UTC"
