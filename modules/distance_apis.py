import datetime
import math

import aiohttp
import numpy as np
import requests
from geopy.distance import distance

from modules.constants import DRIVING_SPEED, WALKING_SPEED, WALK_ENUM
from modules.decorators import cache_data
from modules.logger import logger
from modules.miscellaneous import haversine_distance

TIMEOUT_SECONDS = 5
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount('http://', adapter)
session.mount('https://', adapter)


def make_call_drive(source, destination):
    """
    Placeholder function for distance driving route calculation.
    Currently uses Haversine distance as a temporary solution.
    This should be replaced with actual distance server integration.

    Args:
        source: Tuple of (latitude, longitude) for source location
        destination: Tuple of (latitude, longitude) for destination location

    Returns:
        dict: Response matching distance API format with distance in meters and duration in seconds
    """
    # Get distance in meters and time in minutes
    travel_dist_meters, travel_time_minutes = get_haversine_data(source, destination, 'drive')

    return {
        'code': 'Ok',
        'routes': [{
            'geometry': '',  # Empty geometry as placeholder
            'legs': [{
                'steps': [],
                'distance': travel_dist_meters,
                'duration': travel_time_minutes,
                'summary': '',
                'weight': travel_time_minutes
            }],
            'distance': travel_dist_meters,
            'duration': travel_time_minutes,
            'weight_name': 'duration',
            'weight': travel_time_minutes
        }],
        'waypoints': [{
            'hint': '',
            'distance': 0.0,
            'name': '',
            'location': [source[1], source[0]]
        }, {
            'hint': '',
            'distance': 0.0,
            'name': '',
            'location': [destination[1], destination[0]]
        }]
    }


def make_call_walk(source, destination):
    """
    Placeholder function for distance walking route calculation.
    Currently uses Haversine distance as a temporary solution.
    This should be replaced with actual distance server integration.

    Args:
        source: Tuple of (latitude, longitude) for source location
        destination: Tuple of (latitude, longitude) for destination location

    Returns:
        dict: Response matching distance API format with distance in meters and duration in seconds
    """
    # Get distance in meters and time in seconds
    travel_dist_meters, travel_time_seconds = get_haversine_data(source, destination, 'walk')

    return {
        'code': 'Ok',
        'routes': [{
            'geometry': '',  # Empty geometry as placeholder
            'legs': [{
                'steps': [],
                'distance': travel_dist_meters,
                'duration': travel_time_seconds,
                'summary': '',
                'weight': travel_time_seconds
            }],
            'distance': travel_dist_meters,
            'duration': travel_time_seconds,
            'weight_name': 'duration',
            'weight': travel_time_seconds
        }],
        'waypoints': [{
            'hint': '',
            'distance': 0.0,
            'name': '',
            'location': [source[1], source[0]]
        }, {
            'hint': '',
            'distance': 0.0,
            'name': '',
            'location': [destination[1], destination[0]]
        }]
    }


async def make_api_call(url):
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return url, await response.json()
    except aiohttp.ClientResponseError as e:
        return url, str(e)
    except Exception as e:
        return url, str(e)


def dir_distance(loc1, loc2):
    stst = 6367 * 2 * np.arcsin(np.sqrt(
        np.sin((np.radians(loc1[0]) - math.radians(loc2[0])) / 2) ** 2 + math.cos(
            math.radians(loc2[0])) * np.cos(np.radians(loc1[0])) * np.sin(
            (np.radians(loc1[1]) - math.radians(loc2[1])) / 2) ** 2))
    return stst


def get_haversine_data(src_cords, dst_cords, travel_mode):
    travel_dist = haversine_distance(src_cords[0], src_cords[1], dst_cords[0], dst_cords[1])
    travel_dist *= 1000  # in meter
    travel_time = travel_dist / 2.2 * (WALKING_SPEED if travel_mode == WALK_ENUM else DRIVING_SPEED)
    return travel_dist, travel_time


async def get_multiple_calls_response(coordinates_info, mode):
    """
    Placeholder function for multiple route calculations.
    Uses Haversine distance as a temporary solution.
    This should be replaced with actual distance server integration.

    Args:
        coordinates_info: List of tuples containing source, destination, stop_id, and mode
        mode: Transportation mode ('walk' or 'ptx')

    Returns:
        dict: Route information for each stop_id
    """
    start = datetime.datetime.now()
    results = {}
    coordinate_info_dict = {
        stop_id: (src_cords, dst_cords, mode) for (src_cords, dst_cords, stop_id, mode) in coordinates_info
    }

    if mode == 'walk':
        for stop_id in coordinate_info_dict.keys():
            src_cords, dst_cords, travel_mode = coordinate_info_dict[int(stop_id)]
            travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
            results[int(stop_id)] = {
                'distance': round(travel_dist, 3),
                'duration': round(travel_time, 3),
                'geometry': '',
            }

    if mode == 'ptx':
        # PTX mode is no longer implemented
        for i in range(len(coordinates_info)):
            stop_id = coordinates_info[i][2]
            results[int(stop_id)] = {
                'distance': 0,
                'duration': 0,
                'geometry': '',
                'error': 'PTX mode is not implemented',
            }

    logger.info(f'get_multiple_calls_response_distance_ptx: {datetime.datetime.now() - start}')
    return results


def make_api_call_ptx(url):
    # PTX mode is no longer implemented
    logger.warning("PTX mode API call requested but not implemented")
    return {
        'error': 'PTX mode is not implemented'
    }


def make_api_call2(url):
    @cache_data(cache_key=url)
    def make_cache_call(_url):
        try:
            response = session.get(_url)
            response.raise_for_status()
            return _url, response.json()
        except requests.exceptions.RequestException as e:
            return _url, str(e)

    return make_cache_call(url)


def get_multiple_calls_response_ptx2(coordinates_info, mode):
    # PTX mode is no longer implemented
    logger.warning("PTX mode response requested but not implemented")
    results = {}
    
    for info in coordinates_info:
        stop_id = info[2]
        results[int(stop_id)] = {
            'distance': 0,
            'duration': 0,
            'geometry': '',
            'error': 'PTX mode is not implemented'
        }
    
    return results
    """
    Placeholder function for multiple route calculations (PTX mode).
    Uses Haversine distance as a temporary solution.
    This should be replaced with actual distance server integration.

    Args:
        coordinates_info: List of tuples containing source, destination, stop_id, and mode
        mode: Transportation mode ('walk' or 'ptx')

    Returns:
        dict: Route information for each stop_id
    """
    start = datetime.datetime.now()
    results = {}
    coordinate_info_dict = {
        stop_id: (src_cords, dst_cords, mode) for (src_cords, dst_cords, stop_id, mode) in coordinates_info
    }

    if mode == 'walk':
        for i in range(len(coordinates_info)):
            src_cords = coordinates_info[i][0]
            dst_cords = coordinates_info[i][1]
            stop_id = coordinates_info[i][2]
            travel_mode = 'walk'
            travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
            results[int(stop_id)] = {
                'distance': round(travel_dist, 3),
                'duration': round(travel_time, 3),
                'geometry': '',
            }

    if mode == 'ptx':
        for i in range(len(coordinates_info)):
            src_cords = coordinates_info[i][0]
            dst_cords = coordinates_info[i][1]
            stop_id = coordinates_info[i][2]
            travel_mode = coordinates_info[i][-1]
            travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
            results[int(stop_id)] = {
                'distance': round(travel_dist, 3),
                'duration': round(travel_time, 3),
                'geometry': '',
            }

    logger.info(f'get_multiple_calls_response_distance_ptx2: {datetime.datetime.now() - start}')
    return results


def get_multiple_calls_response_ptx(coordinates_info, mode):
    # PTX mode is no longer implemented
    logger.warning("PTX mode response requested but not implemented")
    results = {}
    
    for info in coordinates_info:
        stop_id = info[2]
        results[int(stop_id)] = {
            'distance': 0,
            'duration': 0,
            'geometry': '',
            'error': 'PTX mode is not implemented'
        }
    
    return results
    """
    distance gives distance in KM, time in
    :param coordinates_info:
    :param mode:
    :return:
    """
    start = datetime.datetime.now()
    results = {}
    coordinate_info_dict = {
        stop_id: (src_cords, dst_cords, mode) for (src_cords, dst_cords, stop_id, mode) in coordinates_info
    }

    try:
        if mode == 'walk':
            for stop_id in coordinate_info_dict.keys():
                src_cords, dst_cords, travel_mode = coordinate_info_dict[int(stop_id)]
                travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
                results[int(stop_id)] = {
                    'distance': round(travel_dist, 3),
                    'duration': round(travel_time, 3),
                    'geometry': '',
                }
        elif mode == 'ptx':
            for i in range(len(coordinates_info)):
                try:
                    src_cords = coordinates_info[i][0]
                    dst_cords = coordinates_info[i][1]
                    stop_id = coordinates_info[i][2]
                    travel_mode = coordinates_info[i][-1]
                    travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
                    results[int(stop_id)] = {
                        'distance': round(travel_dist, 3),
                        'duration': round(travel_time, 3),
                        'geometry': '',
                    }
                except (IndexError, ValueError) as e:
                    print(f"Error processing coordinate {i}: {e}")
                    continue
                except Exception as e:
                    print(f"Unexpected error processing coordinate {i}: {e}")
                    continue

        # Handle any missing stop_ids
        for stop_id in coordinate_info_dict.keys():
            if int(stop_id) not in results:
                try:
                    src_cords, dst_cords, travel_mode = coordinate_info_dict[int(stop_id)]
                    travel_dist, travel_time = get_haversine_data(src_cords, dst_cords, travel_mode)
                    results[int(stop_id)] = {
                        'distance': round(travel_dist, 3),
                        'duration': round(travel_time, 3),
                        'geometry': '',
                    }
                except Exception as e:
                    print(f"Error processing missing stop_id {stop_id}: {e}")

        logger.info(f'get_multiple_calls_response_distance_ptx completed in: {datetime.datetime.now() - start}')
        return results

    except Exception as e:
        logger.error(f'Error in get_multiple_calls_response_distance_ptx: {e}')
        return {}


def get_points(response):
    """
    Extract route points and information from distance response.

    Args:
        response: distance API response dictionary

    Returns:
        dict: Route information including geometry, points, distance and duration
    """
    if not response or 'routes' not in response or not response['routes']:
        return {
            'route': [],
            'start_point': None,
            'end_point': None,
            'distance': 0,
            'total_time': 0
        }

    route = response['routes'][0]
    waypoints = response.get('waypoints', [])

    start_point = None
    end_point = None

    if len(waypoints) >= 2:
        start_point = [waypoints[0]['location'][1], waypoints[0]['location'][0]]
        end_point = waypoints[-1]['location']

    return {
        'route': [],  # Empty as we're not using actual route geometry
        'start_point': start_point,
        'end_point': end_point,
        'distance': route.get('distance', 0),
        'total_time': route.get('duration', 0)
    }


def get_total_time_and_distance(source, destination):
    """
    Get total time and distance for a driving route.

    Args:
        source: Tuple of (latitude, longitude) for source location
        destination: Tuple of (latitude, longitude) for destination location

    Returns:
        tuple: (total_time_minutes, distance_kilometers)
    """
    response = make_call_drive(source, destination)
    if response and response.get('code') == 'Ok' and response.get('routes'):
        route = response['routes'][0]
        # Convert meters to km and seconds to minutes
        return route['duration'] / 60, route['distance'] / 1000
    return 0, 0


def get_walk_info(source, destination):
    """
    Get walking route information.

    Args:
        source: Tuple of (latitude, longitude) for source location
        destination: Tuple of (latitude, longitude) for destination location

    Returns:
        tuple: (geometry, total_time_seconds, distance_meters)
    """
    response = make_call_walk(source, destination)
    if response and response.get('code') == 'Ok' and response.get('routes'):
        route = response['routes'][0]
        return route.get('geometry', []), route['duration'], route['distance']
    return [], 0, 0


def get_total_time_and_distance_walk(source, destination):
    """
    Get total time and distance for a walking route.

    Args:
        source: Tuple of (latitude, longitude) for source location
        destination: Tuple of (latitude, longitude) for destination location

    Returns:
        tuple: (total_time_minutes, distance_kilometers)
    """
    response = make_call_walk(source, destination)
    if response and response.get('code') == 'Ok' and response.get('routes'):
        route = response['routes'][0]
        # Convert meters to km and seconds to minutes
        return route['duration'] / 60, route['distance'] / 1000
    return 0, 0


if __name__ == '__main__':
    _src = (28.54387451715147, 77.27173260014882)
    _dest = (28.545208226484437, 77.26408231313131)

    # resp = make_call_walk(_src, _dest)
    # print(get_walk_info(_src, _dest))
    # rs = get_multiple_calls_response_ptx([(_src, _dest, 0, 'walk')], 'walk')
    # rs = get_multiple_calls_response_ptx([(_src, _dest, 0, 'drive')], 'drive')

    print("with 2")

    rs = get_multiple_calls_response_ptx2([(_src, _dest, 0, 'walk')], 'walk')
    rs = get_multiple_calls_response_ptx2([(_src, _dest, 0, 'drive')], 'drive')
