import math

EARTH_RADIUS_KM = 6371.0


def distance_km(lat1, lon1, lat2, lon2):
    """Distancia sobre la superficie terrestre (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def in_region(lat, lon, min_lat, max_lat, min_lon, max_lon):
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def s_wave_countdown(origin_time, epi_lat, epi_lon, cities, now, s_wave_km_s):
    """Segundos que faltan para que llegue la onda S a cada ciudad (negativo = ya llegó)."""
    result = []
    for name, lat, lon in cities:
        dist = distance_km(epi_lat, epi_lon, lat, lon)
        result.append((name, dist, origin_time + dist / s_wave_km_s - now))
    return result
