from math import isfinite, sqrt

def flow_to_travel_time(
    volume_per_hour: float,
    distance_km: float,
    speed_limit_kmh: float = 60.0,
    intersection_delay_sec: float = 30.0,
) -> float:
    """Estimate travel time (in seconds) from SCATS site A to B.

    Args:
        volume_per_hour: Predicted traffic volume (vehicles/hour) at destination site B
        distance_km: Distance between site A and site B in kilometres
        speed_limit_kmh: Speed limit in km/h (default 60)
        intersection_delay_sec: Delay at each controlled intersection in seconds (default 30)

    Returns:
        Estimated travel time in seconds
    """
    values = (volume_per_hour, distance_km, speed_limit_kmh, intersection_delay_sec)
    if not all(isfinite(value) for value in values) or min(values) < 0 or speed_limit_kmh == 0:
        raise ValueError("Travel-time inputs must be finite and nonnegative, with a positive speed limit")
    a, b = 1.4648375, 93.75
    # The handout assumes the uncongested branch. Flows above capacity
    # are represented by the turning-point speed.
    speed = min(speed_limit_kmh, (b + sqrt(max(0.0, b * b - 4 * a * volume_per_hour))) / (2 * a))
    return 3600 * distance_km / speed + intersection_delay_sec
