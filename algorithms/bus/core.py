"""
The core module for bus algorithm.
"""
from datetime import datetime, timedelta

import geopandas
import pandas as pd

from algorithms.bus.algorithm.core import BusAlgorithms
from algorithms.bus.config import CLUSTERED_STOPS_CSV_FILE_PATH, BUS_ROUTES_DETAILS_DATA_PATH, BUS_STOPS_DF

from algorithms.bus.config import UPDATED_BUS_ROUTES_DF
from algorithms.bus.ranking.core import BusRanking
from algorithms.common.core import BaseParent
from algorithms.walk.core import Walk
from models.models import NearestStop
from models.models import Route, RouteSection, Location
from modules.bus_fare import get_bus_fare
from modules.constants import *
from modules.decorators import cache_data
from modules.logger import logger
from modules.miscellaneous import access_with_handle


class Bus(BaseParent):

    def __init__(self):
        """
        Constructor for Bus class.
        """
        super().__init__()
        self.mode = BUS_ENUM
        self.stop_type = BUS_TYPE_ENUM
        self.gtfs_stops = BUS_STOPS_DF
        self.stops_index_offset = BUS_STOP_INDEX_OFFSET

        self.algorithms = BusAlgorithms()
        self.ranking = BusRanking()
        self.walk = Walk()
        # PTX object removed

        self.stops = self.get_stops(CLUSTERED_STOPS_CSV_FILE_PATH)
        self.bus_route_end_stop_dict = self.get_bus_route_details(BUS_ROUTES_DETAILS_DATA_PATH)

    def turn_off_duplicate(self):
        logger.debug("Turning off duplicate in final result.")
        self.ranking.turn_off_duplicate()

    def turn_on_duplicate(self):
        logger.debug("Turning on duplicate in final result.")
        self.ranking.turn_on_duplicate()

    @cache_data("clustered_stops_csv_file")
    def get_stops(self, stops_file_path: str):
        """
        Get the stops from the given file path.
        Args:
            stops_file_path: The path to the stops file.
        Returns:
            The stops data frame.
        """
        stops_bus = pd.read_csv(stops_file_path)
        stops_bus.rename(columns={'name': 'stop_name', 'lat': 'stop_lat', 'lng': 'stop_lon', 'id': 'stop_id'},
                         inplace=True)
        stops_bus = geopandas.GeoDataFrame(
            stops_bus,
            geometry=geopandas.points_from_xy(stops_bus.stop_lat, stops_bus.stop_lon),
            crs="EPSG:4326"
        )

        return stops_bus

    @cache_data('bus_stops_json')
    def get_stops_json(self):
        stops_bus = pd.read_csv(CLUSTERED_STOPS_CSV_FILE_PATH)
        stops_bus = geopandas.GeoDataFrame(
            stops_bus,
            geometry=geopandas.points_from_xy(stops_bus.lat, stops_bus.lng),
            crs="EPSG:4326"
        )
        stops_bus = stops_bus[['id', 'lat', 'lng', 'name', 'stop_type']]
        stop_list = stops_bus.to_dict('records')
        stop_list = sorted(stop_list, key=lambda x: x['id'])
        return stop_list

    @cache_data('bus_route_detail')
    def get_bus_route_details(self, route_detail_path):
        """
        Get the bus route details.
        Returns:
            The bus route end stop dictionary.
        """

        bus_routes_details = access_with_handle(route_detail_path, pd.read_csv, FileNotFoundError,
                                                place_holder=pd.DataFrame(), args=False, must=False)
        bus_route_end_stop_dict = {}

        for x in bus_routes_details.iterrows():
            bus_route_end_stop_dict[x[1]['route_id_id']] = x[1]['end']
        del bus_routes_details
        return bus_route_end_stop_dict

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):
        logger.debug(f"Getting src dst air for walk for Bus")
        logger.debug(
            f"src:{src},src name:{src_name},src cords:{src_cords},dst:{dst},dst name:{dst_name},dst cords:{dst_cords}"
        )
        if (src.location_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM] or
                dst.location_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM]):
            return []

        if src.location_type != self.stop_type:
            nearest_stops_src = self.algorithms.get_nearest_stops_from_location(
                src.location_value, src.location_type, self.stop_type, src_name, src.tkt_code
            )
        else:
            nearest_stops_src = [
                NearestStop(stop_id=src.location_value, stop_name=src_name, stop_code=src.tkt_code,
                            stop_type=src.location_type, geometry='', distance=0, birds_distance=0, travel_time=0,
                            source_name="")
            ]

        if dst.location_type != self.stop_type:
            nearest_stops_dst = self.algorithms.get_nearest_stops_from_location(
                dst.location_value, dst.location_type, self.stop_type, dst_name, dst.tkt_code
            )
        else:
            nearest_stops_dst = [
                NearestStop(stop_id=dst.location_value, stop_name=dst_name, stop_code=src.tkt_code,
                            stop_type=dst.location_type, geometry='', distance=0, birds_distance=0, travel_time=0,
                            source_name="")
            ]

        all_src_to_dst_combinations = [
            (src, dst) for dst in nearest_stops_dst for src in nearest_stops_src
            if src != dst and src.stop_id != dst.stop_id
        ]

        unique_src_to_dst_combinations = list(all_src_to_dst_combinations)
        return unique_src_to_dst_combinations

    @staticmethod
    def get_route_name(long_name: str, version_cutoff_full_route_name=True) -> str:
        """
        Get the route name.
        Args:
            long_name: The long name of the route.
            version_cutoff_full_route_name: The version cutoff full route name.
        Returns:
            The route name.
        """

        if version_cutoff_full_route_name:
            return long_name.upper()
        else:
            if 'DOWN' in long_name.upper():
                long_name = long_name.upper().replace('DOWN', '')
            if 'UP' in long_name.upper():
                long_name = long_name.upper().replace('UP', '')
            if 'DN' in long_name.upper():
                long_name = long_name.upper().replace('DN', '')
            if '_' in long_name.upper():
                long_name = long_name.upper().replace('_', '')
            return long_name

    def get_color(self, route: Route) -> str:
        """
        Get the color for the route.
        Args:
            route: The route.
        Returns:
            The color for the route.
        """
        agency = route.agency
        vehicle_id = route.vehicle_id
        ac = False # replace here if information available
        if agency.upper() == 'DIMTS':
            if ac:
                return '#0000B3'
            else:
                return '#F5590C'
        elif agency.upper() == 'DTC':
            if ac:
                return '#EB4B4B'
            else:
                return '#80C41C'
        else:
            return '#4D4D4D'

    @staticmethod
    def custom_sort(x) -> tuple:
        """
        Custom sort function.
        Args:
            x: The value.
        Returns:
            The sorted value.
        """
        if x >= 0:
            return 0, x
        else:
            return 1, x

    def get_sorted_on_frequency(self, frequencies: list, routes: list, long_names: list, agency: list) -> tuple:
        """
        Sort all the lists on the basis of frequency.
        Args:
            frequencies: The frequencies list.
            routes: The routes list.
            long_names: The long names list.
            agency: The agency list.
        Returns:
            A tuple of all the sorted lists in the same order as input.
        """
        enumerated_list = list(enumerate(frequencies))
        sorted_frequency_list = sorted(enumerated_list, key=lambda x: self.custom_sort(x[1]))
        original_indices = [item[0] for item in sorted_frequency_list]
        sorted_frequency_list = [x[1] for x in sorted_frequency_list]
        sorted_routes_list = [routes[i] for i in original_indices]
        sorted_long_name_list = [long_names[i] for i in original_indices]
        sorted_agency_list = [agency[i] for i in original_indices]
        return sorted_frequency_list, sorted_routes_list, sorted_long_name_list, sorted_agency_list

    def get_route(self, route_section: RouteSection, mode_to_reach_transit: str) -> Route:
        """
        Get the route for the given route section.
        Args:
            route_section: The route section.
            mode_to_reach_transit: Mode to reach the transit.
        Returns:

        """
        (
            ranked_route_ids,
            vehicle_id,
            departure_time
        ) = route_section.route_id, route_section.vehicle_id, route_section.departure_time

        if ranked_route_ids == [-1]:
            route = self.walk.get_route(route_section, mode_to_reach_transit)

        else:
            route = Route()

            route.route = ''
            route.routes = []

            available_routes = []
            available_long_names = []
            available_frequencies = []
            available_agency = []

            ranked_route_ids = self.ranking.get_ranked_results(ranked_route_ids)
            for idx, ranked_route_id in enumerate(ranked_route_ids):
                val = UPDATED_BUS_ROUTES_DF[
                    UPDATED_BUS_ROUTES_DF.route_id == ranked_route_id
                    ]

                route_name_from_val = val["route_long_name"].item()
                route_number_from_val = val["route_id"].item()
                route_agency_from_val = val["agency_id"].item()

                route_name = self.get_route_name(route_name_from_val)
                with_full_route = False

                if with_full_route:
                    if route_name_from_val not in available_routes:
                        available_routes.append(route_name_from_val)
                        try:
                            available_long_names.append(
                                f" towards {self.bus_route_end_stop_dict[route_number_from_val]}")
                        except KeyError:
                            logger.info(f"Can not find route id {route_number_from_val} in bus route end stop dict.")
                            available_long_names.append(f" towards ")

                        available_frequencies.append(self.ranking.get_current_frequency(ranked_route_id))
                        available_agency.append(route_agency_from_val)
                else:
                    if route_name not in available_routes:
                        available_routes.append(route_name)
                        try:
                            available_long_names.append(
                                f" towards {self.bus_route_end_stop_dict[route_number_from_val]}")
                        except KeyError:
                            logger.info(f"Can not find route id {route_number_from_val} in bus route end stop dict.")
                            available_long_names.append(f" towards ")

                        available_frequencies.append(self.ranking.get_current_frequency(ranked_route_id))
                        available_agency.append(route_agency_from_val)

            (
                sorted_frequency_list, sorted_routes_list, sorted_long_name_list, sorted_agency_list
            ) = self.get_sorted_on_frequency(available_frequencies, available_routes, available_long_names,
                                             available_agency)

            route.routes = sorted_routes_list[:5]
            route.frequency = sorted_frequency_list[0]
            route.long_name = sorted_long_name_list[0]
            route.agency = sorted_agency_list[0]

            route.type = BUS_ENUM
            route.short_name = ''
            route.vehicle_id = vehicle_id[0] if vehicle_id else ''
            route.occupancy = ''
            route.departure_time = departure_time
            route.ending_time = ''
            route.color = self.get_color(route)
            route.description = ''
            route.trip_time = ''
            route.fare = 0
            route.available_options = []
            route.stops = []
            route.polyline = ''

        return route

    # TODO: Change this to get fare of buses
    def get_route_fare(self, route):
        if route[0].parent_info is None:
            return 0
        if route[0].parent_info.get('tkt_code') == route[-1].parent_info.get('tkt_code'):
            return 0
        try:
            if route[-1].route_id[0] == -1:
                return 0
            return get_bus_fare(route[0].parent_info.get('tkt_code'), route[-1].parent_info.get('tkt_code'),
                                route[-1].route_id[0])
        except:
            return 10

    def get_response_type(self, response: list) -> str:
        """
        Get the response type for the given response.
        The response type can be either 'realtime' or 'static'. If the vehicle id contains 'DL' then it is a realtime
        response else it is a static response.
        Args:
            response: The response is a list of
        Returns:
            The response type.
        """
        response_type = 'static'

        return response_type

    def get_response(self, request_data) -> list:
        """
        Get the response for the given request data.
        Args:
            request_data: The request data from user.
            src_to_dst_combinations: The source to destination combinations is a list of list containing NearestStop.
        Returns:
            list: The list of all the possible directions.

        """
        mode_to_reach_transit, _ = request_data.get('mode')

        src: Location = request_data.get(SRC)
        dst: Location = request_data.get(DST)
        src_info: dict = src.location_info
        src_cords: tuple = (src_info[LAT], src_info[LON])
        dst_info: dict = dst.location_info
        dst_cords: tuple = (dst_info[LAT], dst_info[LON])

        time_from_location: str = request_data.get('time')

        def get_self_response():
            logger.info("Collecting self response for Bus.")
            start_time = datetime.strptime(time_from_location, '%H:%M:%S')
            direct_walk_duration_from_src_to_dst = self.get_walk_info(src_cords, dst_cords)

            static_zero_hop_routes: list = []
            static_one_hop_routes: list = []

            src_to_dst_combinations = self.get_nearest_stops(request_data)
            for (source, destination) in src_to_dst_combinations:
                walk_duration_from_src_to_stop: timedelta = timedelta(seconds=source.travel_time)  # in dd:hh:mm:ss
                true_start_time_from_stop: str = (start_time + walk_duration_from_src_to_stop).time().strftime(
                    "%H:%M:%S")
                (
                    static_zero_hop_route,
                    static_one_hop_route
                ) = self.algorithms.get_routes(source, destination, true_start_time_from_stop,
                                               time_from_location)

                static_zero_hop_routes.extend(static_zero_hop_route)
                static_one_hop_routes.extend(static_one_hop_route)

            if not (static_zero_hop_routes or static_one_hop_routes):
                logger.info("Could not find self bus response.")
                possible_directions_self = []
            else:

                static_zero_hop_routes = [route for route in static_zero_hop_routes if route is not None]
                static_one_hop_routes = [route for route in static_one_hop_routes if route is not None]

                ranked_responses: list = self.ranking.rank_result(time_from_location,
                                                                  static_responses_zero=static_zero_hop_routes,
                                                                  static_responses_one=static_one_hop_routes,
                                                                  grouped=True)
                possible_directions_self: list = self.generate_responses(
                    ranked_responses, src, dst, time_from_location, direct_walk_duration_from_src_to_dst,
                    mode_to_reach_transit
                )

            return possible_directions_self

        possible_directions = get_self_response()
        possible_directions = self.sort_on_trip_time(possible_directions)
        return possible_directions if possible_directions else []
