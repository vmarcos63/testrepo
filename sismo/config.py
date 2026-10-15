"""Configuración leída de variables de entorno, con valores por defecto para Panamá."""

import os
from pathlib import Path


def _float(name, default):
    return float(os.environ.get(name, default))


def _int(name, default):
    return int(os.environ.get(name, default))


# Región de interés: Panamá con margen hacia Costa Rica y Colombia.
MIN_LAT = _float("SISMO_MIN_LAT", 5.0)
MAX_LAT = _float("SISMO_MAX_LAT", 11.0)
MIN_LON = _float("SISMO_MIN_LON", -84.0)
MAX_LON = _float("SISMO_MAX_LON", -76.0)

# Fuentes abiertas.
FDSN_STATION_URL = os.environ.get(
    "SISMO_FDSN_STATION_URL", "https://service.iris.edu/fdsnws/station/1/query"
)
SEEDLINK_SERVER = os.environ.get("SISMO_SEEDLINK_SERVER", "rtserve.earthscope.org:18000")
EMSC_WEBSOCKET = os.environ.get(
    "SISMO_EMSC_WEBSOCKET", "wss://www.seismicportal.eu/standing_order/websocket"
)

# Detección por estación (STA/LTA).
STA_S = _float("SISMO_STA_S", 1.0)
LTA_S = _float("SISMO_LTA_S", 30.0)
BUFFER_S = _float("SISMO_BUFFER_S", 90.0)
TRIGGER_ON = _float("SISMO_TRIGGER_ON", 4.0)
TRIGGER_OFF = _float("SISMO_TRIGGER_OFF", 1.5)
HIGHPASS_HZ = _float("SISMO_HIGHPASS_HZ", 1.0)

# Asociación entre estaciones.
MIN_STATIONS = _int("SISMO_MIN_STATIONS", 3)
ASSOC_WINDOW_S = _float("SISMO_ASSOC_WINDOW_S", 20.0)
ASSOC_MAX_DIST_KM = _float("SISMO_ASSOC_MAX_DIST_KM", 250.0)
COOLDOWN_S = _float("SISMO_COOLDOWN_S", 120.0)

# EMSC: magnitud mínima a registrar.
EMSC_MIN_MAG = _float("SISMO_EMSC_MIN_MAG", 3.0)

# Telegram (opcional). Sin token, los avisos solo se imprimen.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

DATA_DIR = Path(os.environ.get("SISMO_DATA_DIR", "data"))
STATIONS_FILE = Path(os.environ.get("SISMO_STATIONS_FILE", DATA_DIR / "stations.json"))

# Ciudades para la cuenta regresiva estimada (nombre, lat, lon).
CITIES = [
    ("Ciudad de Panamá", 8.983, -79.517),
    ("Colón", 9.359, -79.901),
    ("Penonomé", 8.519, -80.357),
    ("Santiago", 8.100, -80.983),
    ("Chitré", 7.961, -80.429),
    ("David", 8.427, -82.431),
]

# Velocidad aproximada de la onda S (el sacudón fuerte), en km/s.
S_WAVE_KM_S = 3.5
