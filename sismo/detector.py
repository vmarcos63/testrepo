"""Detector en silencio: lee señales abiertas en tiempo real (SeedLink) y registra detecciones.

Uso:  python -m sismo.detector      (antes correr python -m sismo.find_stations)
"""

import json
import time

from obspy.clients.seedlink.easyseedlink import create_client

from sismo import config, notify
from sismo.detection import Associator, StationTrigger, Trigger
from sismo.geo import s_wave_countdown

STATUS_EVERY_S = 3600


class Detector:
    def __init__(self, stations):
        self.stations = {f"{s['net']}.{s['sta']}": s for s in stations}
        self.triggers = {
            key: StationTrigger(config.STA_S, config.LTA_S, config.BUFFER_S,
                                config.TRIGGER_ON, config.TRIGGER_OFF, config.HIGHPASS_HZ)
            for key in self.stations
        }
        self.associator = Associator(config.MIN_STATIONS, config.ASSOC_WINDOW_S,
                                     config.ASSOC_MAX_DIST_KM, config.COOLDOWN_S)
        self.data_delay = {}  # estación -> demora del último paquete (s)
        self.last_status = time.time()

    def on_data(self, tr):
        now = time.time()
        key = f"{tr.stats.network}.{tr.stats.station}"
        if key not in self.triggers:
            return
        self.data_delay[key] = now - tr.stats.endtime.timestamp

        onset = self.triggers[key].add(tr)
        if onset is not None:
            s = self.stations[key]
            notify.log_row("triggers.csv", {
                "station": key, "onset_utc": notify.utc(onset),
                "onset": f"{onset:.2f}", "received": f"{now:.2f}",
            })
            detection = self.associator.add(Trigger(key, s["lat"], s["lon"], onset, now))
            if detection:
                self.report(detection, now)

        if now - self.last_status > STATUS_EVERY_S:
            self.report_status()
            self.last_status = now

    def report(self, det, now):
        lat, lon = det.epicenter
        stations = ", ".join(t.station for t in det.triggers)
        notify.log_row("detections.csv", {
            "first_onset_utc": notify.utc(det.first.onset), "detected_utc": notify.utc(now),
            "latency_s": f"{det.latency:.1f}", "lat": f"{lat:.3f}", "lon": f"{lon:.3f}",
            "stations": stations,
        })
        # El origen real es unos segundos antes del primer disparo, así que la cuenta es optimista.
        countdown = s_wave_countdown(det.first.onset, lat, lon, config.CITIES, now, config.S_WAVE_KM_S)
        lines = [
            "🧪 DETECCIÓN EXPERIMENTAL (modo silencio, no es alerta pública)",
            f"Primer disparo: {notify.utc(det.first.onset)}",
            f"Detectado {det.latency:.1f} s después, con {len(det.triggers)} estaciones: {stations}",
            f"Zona aproximada: {lat:.2f}, {lon:.2f}",
            "Llegada estimada del sacudón:",
        ]
        for name, dist, remaining in countdown:
            when = f"en {remaining:.0f} s" if remaining > 0 else "ya llegó"
            lines.append(f"  {name} ({dist:.0f} km): {when}")
        notify.send("\n".join(lines))

    def report_status(self):
        live = {k: d for k, d in self.data_delay.items() if d < 120}
        lines = [f"📡 Estado: {len(live)}/{len(self.stations)} estaciones enviando datos"]
        for key, delay in sorted(live.items(), key=lambda kv: kv[1]):
            lines.append(f"  {key}: demora {delay:.1f} s")
        print("\n".join(lines), flush=True)
        notify.log_row("status.csv", {
            "time_utc": notify.utc(time.time()), "live": len(live), "total": len(self.stations),
        })


def run():
    stations = json.loads(config.STATIONS_FILE.read_text())
    if not stations:
        raise SystemExit("No hay estaciones en el archivo; correr primero python -m sismo.find_stations")
    detector = Detector(stations)
    backoff = 5
    while True:
        try:
            client = create_client(config.SEEDLINK_SERVER, on_data=detector.on_data)
            for s in stations:
                client.select_stream(s["net"], s["sta"], f"{s['loc']}{s['cha']}")
            print(f"Conectado a {config.SEEDLINK_SERVER} con {len(stations)} estaciones", flush=True)
            backoff = 5
            client.run()
        except Exception as exc:  # la conexión se cae: reintentar siempre
            print(f"[seedlink] {exc!r}; reintento en {backoff} s", flush=True)
        time.sleep(backoff)
        backoff = min(backoff * 2, 300)


if __name__ == "__main__":
    run()
