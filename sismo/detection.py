"""Lógica de detección, independiente de la red: disparo por estación (STA/LTA) y asociación."""

from dataclasses import dataclass, field

import numpy as np
from obspy.signal.trigger import recursive_sta_lta

from sismo.geo import distance_km


@dataclass
class Trigger:
    station: str
    lat: float
    lon: float
    onset: float  # momento del disparo según los datos (epoch UTC)
    received: float  # momento en que lo procesamos (epoch UTC)


@dataclass
class Detection:
    triggers: list = field(default_factory=list)

    @property
    def first(self):
        return self.triggers[0]

    @property
    def epicenter(self):
        """Estimación gruesa: promedio de las primeras 3 estaciones en dispararse."""
        first = self.triggers[:3]
        return (sum(t.lat for t in first) / len(first), sum(t.lon for t in first) / len(first))

    @property
    def latency(self):
        """Segundos desde el primer disparo hasta que confirmamos la detección."""
        return self.triggers[-1].received - self.first.onset


class StationTrigger:
    """Mantiene un buffer de señal de una estación y detecta inicios de sacudón con STA/LTA."""

    def __init__(self, sta_s, lta_s, buffer_s, on, off, highpass_hz):
        self.sta_s, self.lta_s, self.buffer_s = sta_s, lta_s, buffer_s
        self.on, self.off, self.highpass_hz = on, off, highpass_hz
        self.trace = None
        self.triggered = False

    def add(self, tr):
        """Agrega un paquete de datos. Devuelve el instante de inicio si hubo disparo, si no None."""
        tr = tr.copy()
        tr.data = tr.data.astype(np.float64)
        sr = tr.stats.sampling_rate
        if self.trace is None or abs(tr.stats.starttime - self.trace.stats.endtime - 1 / sr) > 1.5 / sr:
            # Primer paquete o hueco en los datos: empezamos de nuevo.
            self.trace = tr
            self.triggered = False
            return None
        self.trace.data = np.concatenate([self.trace.data, tr.data])
        excess = len(self.trace.data) - int(self.buffer_s * sr)
        if excess > 0:
            self.trace.data = self.trace.data[excess:]
            self.trace.stats.starttime += excess / sr

        nlta = int(self.lta_s * sr)
        if len(self.trace.data) < 2 * nlta:
            return None  # todavía no hay suficiente historia para un LTA estable

        filtered = self.trace.copy()
        filtered.detrend("demean")
        filtered.filter("highpass", freq=self.highpass_hz, corners=2, zerophase=False)
        cft = recursive_sta_lta(filtered.data, int(self.sta_s * sr), nlta)

        new = cft[-len(tr.data):]
        offset = len(cft) - len(tr.data)
        for i, value in enumerate(new):
            if not self.triggered and value >= self.on:
                self.triggered = True
                return float(self.trace.stats.starttime.timestamp + (offset + i) / sr)
            if self.triggered and value <= self.off:
                self.triggered = False
        return None


class Associator:
    """Declara un sismo cuando varias estaciones cercanas se disparan casi juntas."""

    def __init__(self, min_stations, window_s, max_dist_km, cooldown_s):
        self.min_stations = min_stations
        self.window_s = window_s
        self.max_dist_km = max_dist_km
        self.cooldown_s = cooldown_s
        self.recent = []
        self.last_detection_onset = None

    def add(self, trig):
        self.recent = [t for t in self.recent if trig.onset - t.onset <= self.window_s]
        if any(t.station == trig.station for t in self.recent):
            return None  # una estación cuenta una sola vez por ventana
        self.recent.append(trig)
        self.recent.sort(key=lambda t: t.onset)

        first = self.recent[0]
        if self.last_detection_onset is not None and first.onset - self.last_detection_onset < self.cooldown_s:
            return None
        cluster = [
            t for t in self.recent
            if t.onset - first.onset <= self.window_s
            and distance_km(first.lat, first.lon, t.lat, t.lon) <= self.max_dist_km
        ]
        if len(cluster) < self.min_stations:
            return None
        self.last_detection_onset = first.onset
        self.recent = []
        return Detection(triggers=cluster)
