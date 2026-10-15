import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from obspy import Trace, UTCDateTime

from sismo import config
from sismo.detection import Associator, StationTrigger, Trigger
from sismo.detector import Detector
from sismo.emsc_listener import parse_event
from sismo.find_stations import parse_channels, pick_best_per_station
from sismo.geo import distance_km, s_wave_countdown

START = UTCDateTime(2026, 10, 9, 17, 56, 0)


def packets(data, sr=100.0, packet_s=5.0):
    n = int(packet_s * sr)
    for i in range(0, len(data), n):
        yield Trace(data=data[i:i + n], header={
            "network": "XX", "station": "TEST", "channel": "HHZ",
            "sampling_rate": sr, "starttime": START + i / sr,
        })


class StationTriggerTest(unittest.TestCase):
    def make(self):
        return StationTrigger(sta_s=1, lta_s=30, buffer_s=90, on=4, off=1.5, highpass_hz=1)

    def test_detects_onset_of_strong_shaking(self):
        rng = np.random.default_rng(0)
        data = rng.normal(0, 1, 120 * 100)
        data[80 * 100:90 * 100] += rng.normal(0, 30, 10 * 100)
        st = self.make()
        onsets = [o for tr in packets(data) if (o := st.add(tr)) is not None]
        self.assertEqual(len(onsets), 1)
        self.assertAlmostEqual(onsets[0] - START.timestamp, 80, delta=1)

    def test_noise_alone_does_not_trigger(self):
        data = np.random.default_rng(1).normal(0, 1, 300 * 100)
        st = self.make()
        self.assertEqual([o for tr in packets(data) if (o := st.add(tr)) is not None], [])

    def test_gap_resets_buffer(self):
        st = self.make()
        st.add(Trace(np.zeros(500), header={"sampling_rate": 100, "starttime": START}))
        st.add(Trace(np.zeros(500), header={"sampling_rate": 100, "starttime": START + 60}))
        self.assertEqual(st.trace.stats.starttime, START + 60)


class AssociatorTest(unittest.TestCase):
    def make(self):
        return Associator(min_stations=3, window_s=20, max_dist_km=250, cooldown_s=120)

    def test_three_nearby_stations_make_a_detection(self):
        a = self.make()
        self.assertIsNone(a.add(Trigger("A", 7.4, -80.4, 100.0, 104.0)))
        self.assertIsNone(a.add(Trigger("B", 7.9, -80.4, 105.0, 109.0)))
        det = a.add(Trigger("C", 8.1, -81.0, 110.0, 113.0))
        self.assertIsNotNone(det)
        self.assertEqual(det.first.station, "A")
        self.assertAlmostEqual(det.latency, 13.0)

    def test_same_station_counts_once(self):
        a = self.make()
        for onset in (100, 102, 104):
            self.assertIsNone(a.add(Trigger("A", 7.4, -80.4, onset, onset)))

    def test_far_or_late_triggers_are_ignored(self):
        a = self.make()
        a.add(Trigger("A", 7.4, -80.4, 100.0, 100.0))
        a.add(Trigger("FAR", 15.0, -90.0, 101.0, 101.0))
        self.assertIsNone(a.add(Trigger("LATE", 7.5, -80.5, 150.0, 150.0)))

    def test_cooldown_avoids_duplicate_detections(self):
        a = self.make()
        for i, name in enumerate("ABC"):
            det = a.add(Trigger(name, 7.4 + i * 0.1, -80.4, 100.0 + i, 100.0 + i))
        self.assertIsNotNone(det)
        for i, name in enumerate("DEF"):
            self.assertIsNone(a.add(Trigger(name, 7.4 + i * 0.1, -80.4, 110.0 + i, 110.0 + i)))


class DetectorEndToEndTest(unittest.TestCase):
    def test_three_stations_shaking_produce_one_detection(self):
        stations = [
            {"net": "XX", "sta": f"S{i}", "loc": "", "cha": "HHZ", "lat": 7.4 + i * 0.2, "lon": -80.4}
            for i in range(3)
        ]
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(config, "DATA_DIR", Path(tmp)), \
                mock.patch("sismo.notify.send") as send:
            det = Detector(stations)
            rng = np.random.default_rng(2)
            for i, s in enumerate(stations):
                data = rng.normal(0, 1, 120 * 100)
                start = (80 + 3 * i) * 100
                data[start:start + 1000] += rng.normal(0, 30, 1000)
                for tr in packets(data):
                    tr.stats.station = s["sta"]
                    det.on_data(tr)
            self.assertEqual(send.call_count, 1)
            self.assertIn("DETECCIÓN EXPERIMENTAL", send.call_args[0][0])
            with (Path(tmp) / "detections.csv").open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["stations"], "XX.S0, XX.S1, XX.S2")


class GeoTest(unittest.TestCase):
    def test_tonosi_to_panama_city(self):
        self.assertAlmostEqual(distance_km(7.40, -80.44, 8.983, -79.517), 203, delta=5)

    def test_countdown(self):
        (name, dist, remaining), = s_wave_countdown(0, 7.40, -80.44, [("PTY", 8.983, -79.517)], 10, 3.5)
        self.assertAlmostEqual(remaining, dist / 3.5 - 10)


class ParsingTest(unittest.TestCase):
    def test_parse_and_pick_channels(self):
        text = (
            "#Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|"
            "SensorDescription|Scale|ScaleFreq|ScaleUnits|SampleRate|StartTime|EndTime\n"
            "XX|AAA||EHZ|8.0|-80.0|10|0|0|-90|s|1|1|M/S|100|2020-01-01T00:00:00|\n"
            "XX|AAA|00|HHZ|8.0|-80.0|10|0|0|-90|s|1|1|M/S|100|2020-01-01T00:00:00|\n"
            "XX|BBB||HNZ|9.0|-79.0|10|0|0|-90|s|1|1|M/S2|200|2020-01-01T00:00:00|\n"
            "XX|BBB||HNE|9.0|-79.0|10|0|0|0|s|1|1|M/S2|200|2020-01-01T00:00:00|\n"
        )
        picked = pick_best_per_station(parse_channels(text))
        self.assertEqual([(s["sta"], s["loc"], s["cha"]) for s in picked],
                         [("AAA", "00", "HHZ"), ("BBB", "", "HNZ")])

    def test_emsc_event_in_region(self):
        msg = {"action": "create", "data": {"properties": {
            "lat": 7.4, "lon": -80.4, "mag": 6.6, "time": "2026-10-09T20:25:00.0Z",
            "unid": "x", "flynn_region": "SOUTH OF PANAMA"}}}
        event = parse_event(json.dumps(msg))
        self.assertEqual(event["mag"], 6.6)
        self.assertEqual(event["origin"], UTCDateTime(2026, 10, 9, 20, 25).timestamp)

    def test_emsc_event_outside_region_or_small(self):
        far = {"data": {"properties": {"lat": 35, "lon": 139, "mag": 6, "time": "2026-10-09T00:00:00Z"}}}
        small = {"data": {"properties": {"lat": 8, "lon": -80, "mag": config.EMSC_MIN_MAG - 1,
                                         "time": "2026-10-09T00:00:00Z"}}}
        self.assertIsNone(parse_event(json.dumps(far)))
        self.assertIsNone(parse_event(json.dumps(small)))


if __name__ == "__main__":
    unittest.main()
