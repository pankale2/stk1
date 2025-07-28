from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time
import threading

class TradingScheduler:
    def __init__(self, strategy_func, exit_func):
        self.scheduler = BackgroundScheduler()
        self.strategy_func = strategy_func
        self.exit_func = exit_func
        self.add_jobs()

    def add_jobs(self):
        # Run strategy every 2 minutes between 9:30 and 14:30, weekdays, skip market holidays
        def strategy_wrapper():
            from market_holidays import is_market_holiday
            now = datetime.now()
            if is_market_holiday():
                print("[scheduler] Skipping strategy: market holiday.")
                return
            # Only run between 9:30 and 14:30
            if not (time(9,30) <= now.time() <= time(15,15)):
                print("[scheduler] Skipping strategy: outside trading hours.")
                return
            result = self.strategy_func()
            print(f"[scheduler] Strategy run at {now.strftime('%H:%M:%S')}. Result: {result if result else 'OK'}")

        self.scheduler.add_job(strategy_wrapper, 'cron', day_of_week='mon-fri', hour='9-14', minute='*/2',
                               start_date='2024-01-01', end_date='2030-01-01',
                               id='strategy_job')
        # Exit all at 14:30
        self.scheduler.add_job(self.exit_func, 'cron', day_of_week='mon-fri', hour=14, minute=30,
                               start_date='2024-01-01', end_date='2030-01-01',
                               id='exit_job')

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()
