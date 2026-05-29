from apscheduler.schedulers.background import BackgroundScheduler

from app.services.alert_service import scan_alerts
from app.services.price_service import get_latest_price

scheduler = BackgroundScheduler(timezone="UTC")


def collect_and_scan():
    price = get_latest_price()
    scan_alerts(price)


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(collect_and_scan, "interval", seconds=10, id="gold_collect_scan", replace_existing=True)
    scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
