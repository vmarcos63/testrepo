"""Escucha el websocket de EMSC y registra cada sismo de la región, con su demora de publicación.

Uso:  python -m sismo.emsc_listener
"""

import asyncio
import json
import time
from datetime import datetime

import websockets

from sismo import config, notify
from sismo.geo import in_region


def parse_event(message):
    """Devuelve un dict con los datos del sismo, o None si no corresponde a la región."""
    msg = json.loads(message)
    props = msg.get("data", {}).get("properties", {})
    lat, lon, mag = props.get("lat"), props.get("lon"), props.get("mag")
    if lat is None or lon is None or mag is None:
        return None
    if not in_region(lat, lon, config.MIN_LAT, config.MAX_LAT, config.MIN_LON, config.MAX_LON):
        return None
    if mag < config.EMSC_MIN_MAG:
        return None
    origin = datetime.fromisoformat(props["time"].replace("Z", "+00:00")).timestamp()
    return {
        "action": msg.get("action", ""),
        "id": props.get("unid", ""),
        "origin": origin,
        "lat": lat,
        "lon": lon,
        "mag": mag,
        "region": props.get("flynn_region", ""),
    }


def handle(message):
    event = parse_event(message)
    if event is None:
        return
    now = time.time()
    delay = now - event["origin"]
    notify.log_row("emsc.csv", {
        "action": event["action"], "id": event["id"], "origin_utc": notify.utc(event["origin"]),
        "received_utc": notify.utc(now), "delay_s": f"{delay:.0f}", "mag": event["mag"],
        "lat": event["lat"], "lon": event["lon"], "region": event["region"],
    })
    if event["action"] == "create":
        notify.send(
            f"🌎 EMSC: M{event['mag']:.1f} {event['region']}\n"
            f"Origen {notify.utc(event['origin'])}, publicado {delay / 60:.1f} min después"
        )


async def listen():
    backoff = 5
    while True:
        try:
            async with websockets.connect(config.EMSC_WEBSOCKET, ping_interval=15) as ws:
                print(f"Conectado a {config.EMSC_WEBSOCKET}", flush=True)
                backoff = 5
                async for message in ws:
                    handle(message)
        except Exception as exc:
            print(f"[emsc] {exc!r}; reintento en {backoff} s", flush=True)
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 300)


if __name__ == "__main__":
    asyncio.run(listen())
