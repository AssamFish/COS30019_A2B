"""
travel_time.py - Convert predicted traffic flow to travel time.

Assumptions:
- Speed limit: 60 km/h on all links
- Intersection delay: 30 seconds per controlled intersection
- Travel time formula based on VicRoads conversion document
"""


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
    # Free-flow travel time
    free_flow_time = (distance_km / speed_limit_kmh) * 3600  # convert hours to seconds

    # TODO: Apply the VicRoads traffic flow to travel time conversion formula
    # Adjust free_flow_time based on volume_per_hour
    # See "Traffic Flow to Travel Time Conversion v1.0.PDF"

    travel_time = free_flow_time + intersection_delay_sec

    return travel_time
