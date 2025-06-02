import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from geopy.distance import distance

from modules.constants import *
from modules.logger import logger
from modules.distance_apis import get_walk_info


class BaseParent(ABC):

    def get_stops(self, stops_file_path):
        pass

    def get_nearest_stops(self, request_data):
        """
        Get the nearest stops for the given request data.
        Args:
            request_data: The request data.
        Returns:
            The nearest stops.
        """
        logger.debug("In nearest stops function.")

        mode_to_reach_transit, _ = request_data.get('mode')
        max_fare = request_data.get('max_fare')
        time = request_data.get('time')

        src = request_data.get(SRC)
        src_name = request_data.get(SRC_NAME)
        src_info = src.location_info
        src_cords = (src_info[LAT], src_info[LON])

        dst = request_data.get(DST)
        dst_name = request_data.get(DST_NAME)
        dst_info = dst.location_info
        dst_cords = (dst_info[LAT], dst_info[LON])
        logger.debug(
            f"src:{src},src name:{src_name},src cords:{src_cords},dst:{dst},dst name:{dst_name},dst cords:{dst_cords}"
        )

        if mode_to_reach_transit == WALK_ENUM:
            return self.get_src_dst_for_walk(src, src_name, src_cords, dst, dst_name, dst_cords)
        else:
            return []

    @abstractmethod
    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):
        pass

    @abstractmethod
    def get_response_type(self, response):
        pass

    @abstractmethod
    def get_route(self, route_section, mode_to_reach_transit):
        pass

    @staticmethod
    def lm_fare(row):
        if row['mode'] == 'drive':
            return math.ceil(row['distance'] - 1) * FARE_NEXT_KM + FARE_FIRST_KM
        else:
            return 0

    @staticmethod
    def lm_dir_distance(loc, lat2, lon2):
        return distance(loc, [lat2, lon2]).km

    @staticmethod
    def get_peak_off_peak_category(x):
        if x < 8:
            category = "non_peak_1"
        elif x < 12:
            category = "peak_1"
        elif x < 17:
            category = "non_peak_2"
        elif x < 21:
            category = "peak_2"
        else:
            category = "non_peak_3"
        return category

    def generate_one_response(self, rt_idx, rt, src, dst, mode_to_reach_transit):

        try:
            route = self.get_route(rt[1], mode_to_reach_transit)
        except Exception as e:
            logger.debug(f"Error {e} in getting route {rt[1].route_id[0]}")
            logger.info(f"Error in getting route {rt[1].route_id[0]}")
            return None

        geometry = rt[-1].geometry
        distance = round(rt[-1].distance * 1000) if rt[-1].distance != '' else 0
        trip_time = round(rt[-1].travel_time_of_edge / 60)

        stops = []
        for leg_idx, leg in enumerate(rt):
            if leg_idx == 0:
                continue

            if len(stops) == 0:
                if rt_idx == 0 and leg.route_id in [-1, -50, [-50], [-1]]:
                    if isinstance(src.location_value, int):
                        stops.append(src.location_info)
                    else:
                        stops.append({
                            'id': -1,
                            LAT: src.location_info[LAT],
                            LON: src.location_info[LON],
                            'name': src.location_name}
                        )
                else:
                    stops.append(leg.parent_info)

            if leg_idx == len(rt) - 1:
                if leg.child_node < 0:
                    if len(dst) == 1:
                        stops.append(dst.location_info)
                    else:
                        stops.append({
                            'id': -2,
                            LAT: dst.location_info[LAT],
                            LON: dst.location_info[LON],
                            'name': dst.location_name,
                        })
                else:
                    stops.append(leg.child_info)
            else:
                stops.append(leg.child_info)


        route.fare = self.get_route_fare(rt)

        route.trip_time = max(1, trip_time)
        route.stops = stops
        route.polyline = geometry
        route.distance = distance

        return route

    def generate_responses(self, responses, src, dst, query_time, direct_walk_duration, mode_to_reach_transit):

        possible_directions = []

        for res in responses:  # All routes
            total_fare = 0
            directions = {'routes': []}
            total_trip_time_in_seconds = self.subtract_times(res[-1][-1].arrival_time, res[0][0].arrival_time)

            # if direct_walk_duration is not None and total_trip_time_in_seconds >= direct_walk_duration:
            #     continue

            #  Processing for 1 whole route list
            routes = []
            for rt_idx, rt in enumerate(res):  # individual route
                route = self.generate_one_response(rt_idx, rt, src, dst, mode_to_reach_transit)

                if route is None:
                    continue

                total_fare = max(-1, total_fare + route.fare)
                routes.append(route.to_dict())
                directions['routes'] = routes

            response_type = self.get_response_type(res)

            try:
                total_trip_time = (total_trip_time_in_seconds // 60)
            except Exception as e:
                logger.debug(f"Error {e} in calculating total trip time")
                logger.info(f"Error in calculating total trip time")
                total_trip_time = 0

            possible_directions.append(
                {
                    'directions': directions,
                    'fare_unit': '₹',
                    'trip_time': total_trip_time,
                    'total_fare': float(total_fare),
                    'response_type': response_type,
                    'reach_by': res[-1][-1].arrival_time,
                    "time_unit": "min",
                    'request_time': query_time,
                    'created_at': datetime.now(),
                    "route_description": "Alternate route",
                    'total_fare_range': f'₹{float(total_fare)}'
                }
            )

        return possible_directions

    @abstractmethod
    def get_response(self, request_data):
        pass

    @abstractmethod
    def get_route_fare(self, route):
        pass

    @abstractmethod
    def get_color(self, route):
        pass

    @staticmethod
    def sort_on_trip_time(directions_options):
        sorted_options = sorted(directions_options, key=lambda x: x['trip_time'])
        return sorted_options

    @staticmethod
    def get_walk_info(src_coords, dst_coords):

        try:
            walk_geometry, walk_time, walk_distance = get_walk_info(src_coords, dst_coords)
        except (KeyError, IndexError) as e:
            logger.debug(f"Error {e} in getting walk info")
            logger.info(f"Error in getting walk info, unable to assign walk time from {src_coords} to {dst_coords}")
            walk_geometry, walk_time, walk_distance = None, None, None

        return walk_time

    @staticmethod
    def subtract_times(t1, t2):
        datetime2 = datetime.strptime(t2, "%H:%M:%S")
        datetime1 = datetime.strptime(t1, "%H:%M:%S")

        time_diff = datetime1 - datetime2
        # Convert the time difference to seconds
        time_diff_seconds = time_diff.total_seconds()

        return time_diff_seconds

    @staticmethod
    def add_times(t1, t1_min):
        datetime1 = datetime.strptime(t1, "%H:%M:%S")
        time_delta = timedelta(minutes=t1_min)

        time_sum = datetime1 + time_delta

        return datetime.strftime(time_sum, "%H:%M:%S")
