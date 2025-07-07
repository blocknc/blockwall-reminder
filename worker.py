# worker.py (for Render background worker)
from tasks import start_scheduler

if __name__ == '__main__':
    print("Starting background scheduler...")
    start_scheduler()

    # Keep the process alive
    import time
    while True:
        time.sleep(60)
