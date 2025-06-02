import numpy as np
import asyncio
from models.models import NearestStop
from modules.distance_apis import get_multiple_calls_response
from modules.miscellaneous import haversine_distance
from modules.constants import WALKING_SPEED


def find_stops_within_radius(query_coords, df, radius, param_dist='distance', param_dur='duration'):
    # radius in kilometers
    """
    given the query coordinates, data df and radius (in km), the function returns the dataframe of vehicles
    within radius of the queried coordinates
    :param query_coords: tuple of lat, long
    :param df: stops data dataframe
    :param radius: distance threshold in km
    :return: dataframe of stops records within radius of given query coords
    """

    q_lat = query_coords[0]
    q_lng = query_coords[1]

    vehicle_lats = df['stop_lat'].values.astype(float)
    vehicle_lngs = df['stop_lon'].values.astype(float)

    stst = haversine_distance(q_lat, q_lng, vehicle_lats, vehicle_lngs)
    df[param_dist] = stst
    df[param_dur] = stst / WALKING_SPEED

    bus_record_indices_within_radius = np.where(stst <= radius)[0]

    return df.iloc[bus_record_indices_within_radius]


def get_centroids_given_location(coordinates, cnt, mode_object):
    initial_radius = 0.5
    while True:
        nearest_stops = find_stops_within_radius(coordinates, mode_object.stops, initial_radius)

        if len(nearest_stops) > cnt:
            break
        else:
            initial_radius = initial_radius * 2

    if 'tkr_code' not in nearest_stops.columns:
        nearest_stops['tkt_code'] = ''

    nearest_stops_list = []
    walk_results = asyncio.run(
        get_multiple_calls_response([
            [
                coordinates,
                [stop['stop_lat'], stop['stop_lon']],
                stop['stop_id'],
                'walk'
            ] for idx, stop in nearest_stops.iterrows()
        ], mode='walk')
    )

    if walk_results is None:
        nearest_stops['geometry'] = ''

    nearest_stops_dict = nearest_stops.set_index('stop_id').T.to_dict()

    for stop_id, response in walk_results.items():
        if response == -1:
            response = nearest_stops_dict[stop_id]
        try:
            stop_type_from_walk = nearest_stops_dict[stop_id]['stop_type']
        except KeyError as e:
            stop_type_from_walk = mode_object.mode
            print(f"Error: {e} not found in walk results for stop_id: {stop_id} and mode: {mode_object.mode}.")
            print(f"Modifying {e} to the default mode: ", stop_type_from_walk)

        try:
            nearest_stop = NearestStop(
                stop_id=stop_id,
                stop_name=nearest_stops_dict[stop_id]['stop_name'],
                stop_type=stop_type_from_walk,
                stop_code=nearest_stops_dict[stop_id]['tkt_code'],
                geometry=response['geometry'],
                distance=response['distance'] / 1000, birds_distance= response['distance'] / 1000,
                travel_time=response['duration'], source_name='Your location')

            nearest_stops_list.append(nearest_stop)

        except Exception as e:
            print('walk error {}'.format(e))

    updated_nearest_stops = sorted(nearest_stops_list, key=lambda stop: stop.distance)

    return updated_nearest_stops[:cnt]
