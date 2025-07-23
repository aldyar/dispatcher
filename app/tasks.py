from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from function.operator_function import OperatorFunction
from router.lead_router import main_weely  # или откуда у тебя main_weely

scheduler = AsyncIOScheduler()

def start_jobs():
    # Каждые 5 минут
    scheduler.add_job(
        OperatorFunction.update_operators_online_status,
        CronTrigger(minute="*/5")
    )

    # Каждую неделю в понедельник в 3:00
    scheduler.add_job(
        main_weely,
        CronTrigger(day_of_week="mon", hour=3, minute=0)
    )

    scheduler.start()
