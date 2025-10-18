#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

STOP = False


def handle_signal(signum, frame):
    global STOP
    logging.info("Signal %s received, stopping after current run...", signum)
    STOP = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def run_server_status(script_path):
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=False)
        if result.stdout:
            logging.info("server_status stdout:\n%s", result.stdout.strip())
        if result.stderr:
            logging.warning("server_status stderr:\n%s", result.stderr.strip())
        if result.returncode != 0:
            logging.error("server_status exited with code %s", result.returncode)
    except Exception as e:
        logging.exception("Failed to run server_status: %s", e)


def main(interval_seconds=30):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_status_path = os.path.join(script_dir, "server_status.py")
    if not os.path.isfile(server_status_path):
        logging.error("Cannot find server_status.py at %s", server_status_path)
        sys.exit(1)

    logging.info("Starting cron simulator, running %s every %s seconds", server_status_path, interval_seconds)
    while not STOP:
        start = time.time()
        run_server_status(server_status_path)
        if STOP:
            break
        elapsed = time.time() - start
        sleep_for = max(0, interval_seconds - elapsed)
        time.sleep(sleep_for)

    logging.info("Cron simulator stopped.")


if __name__ == "__main__":
    main(30)