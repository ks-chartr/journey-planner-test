"""
This module contains utility functions for the serializers.
"""

from shapely.geometry import Point
from env_middlewares.common_env import LOCATION
from modules.constants import BOUNDARIES, OTHER_COORDINATES
from rest_framework import serializers


def is_in_location(lat_lon: tuple) -> bool:
    """
    Check if the given latitude and longitude is within the location boundary.
    Args:
        lat_lon: Tuple of latitude and longitude.
    Returns:
        bool: True if the given latitude and longitude is within the location boundary, False otherwise.
    """

    try:
        location_boundaries = BOUNDARIES[LOCATION]
        point = Point(lat_lon)
        return location_boundaries.contains(point) or lat_lon in OTHER_COORDINATES

    except KeyError:
        raise serializers.ValidationError(f"{lat_lon} is not in {LOCATION}.")
