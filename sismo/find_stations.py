"""Busca estaciones sísmicas abiertas y activas en la región y las guarda en data/stations.json.

Uso:  python -m sismo.find_stations
"""

import json
from datetime import datetime, timezone

import requests

from sismo import config

# Preferencia de canal vertical: banda ancha > acelerómetro > período corto.
CHANNEL_PREFERENCE = ["HHZ", "BHZ", "HNZ", "ENZ", "EHZ", "SHZ"]


def parse_channels(text):
    """Parsea la respuesta FDSN en formato texto (level=channel)."""
    channels = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("|")
        if len(cols) < 15:
            continue
        channels.append({
            "net": cols[0],
            "sta": cols[1],
            "loc": cols[2],
            "cha": cols[3],
            "lat": float(cols[4]),
            "lon": float(cols[5]),
            "sample_rate": float(cols[14]) if cols[14] else 0.0,
        })
    return channels


def pick_best_per_station(channels):
    """Se queda con un canal vertical por estación, según CHANNEL_PREFERENCE."""
    best = {}
    for ch in channels:
        if ch["cha"] not in CHANNEL_PREFERENCE:
            continue
        key = (ch["net"], ch["sta"])
        rank = CHANNEL_PREFERENCE.index(ch["cha"])
        if key not in best or rank < CHANNEL_PREFERENCE.index(best[key]["cha"]):
            best[key] = ch
    return sorted(best.values(), key=lambda c: (c["net"], c["sta"]))


def fetch_channels():
    params = {
        "minlat": config.MIN_LAT,
        "maxlat": config.MAX_LAT,
        "minlon": config.MIN_LON,
        "maxlon": config.MAX_LON,
        "level": "channel",
        "channel": ",".join(CHANNEL_PREFERENCE),
        "endafter": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "includerestricted": "false",
        "format": "text",
    }
    resp = requests.get(config.FDSN_STATION_URL, params=params, timeout=60)
    if resp.status_code == 204:
        return []
    resp.raise_for_status()
    return parse_channels(resp.text)


def main():
    stations = pick_best_per_station(fetch_channels())
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.STATIONS_FILE.write_text(json.dumps(stations, indent=2))

    print(f"{len(stations)} estaciones abiertas y activas en la región:")
    for s in stations:
        print(f"  {s['net']}.{s['sta']}.{s['loc'] or '--'}.{s['cha']}  "
              f"({s['lat']:.3f}, {s['lon']:.3f})  {s['sample_rate']:g} Hz")
    print(f"\nGuardadas en {config.STATIONS_FILE}")
    print("Ojo: estar en el catálogo no garantiza que transmitan en tiempo real; "
          "el detector registra cuáles envían datos.")


if __name__ == "__main__":
    main()
