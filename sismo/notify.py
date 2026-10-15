"""Avisos por Telegram (en un hilo aparte, para no frenar la detección) y registro en CSV."""

import csv
import queue
import threading
from datetime import datetime, timezone

import requests

from sismo import config

_queue = queue.Queue()


def _worker():
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    while True:
        text = _queue.get()
        try:
            requests.post(url, data={"chat_id": config.TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        except requests.RequestException as exc:
            print(f"[telegram] error: {exc}", flush=True)


if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
    threading.Thread(target=_worker, daemon=True).start()


def send(text):
    print(text, flush=True)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        _queue.put(text)


def log_row(filename, row):
    """Agrega una fila a data/<filename>, escribiendo el encabezado si el archivo es nuevo."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = config.DATA_DIR / filename
    is_new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def utc(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
