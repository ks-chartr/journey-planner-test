import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import geopandas
import pandas as pd

from algorithms.bus.core import Bus
from algorithms.common.config import ALL_STOPS_PATH
from algorithms.common.core import BaseParent
from algorithms.metro.core import Metro
from algorithms.multimodal.algorithm.core import MultiModalAlgorithms
from algorithms.multimodal.ranking.core import MultiModalRanking
from algorithms.walk.core import Walk
from models.models import NearestStop
from modules.bus_fare import get_bus_fare
from modules.constants import *
from modules.logger import logger


class MultiModal(BaseParent):

    def __init__(self):
        super().__init__()
        self.mode = MULTI_ENUM

        self.stops = self.get_stops(ALL_STOPS_PATH)

        self.metro_object = Metro()
        self.bus_object = Bus()
        self.algorithms = MultiModalAlgorithms()
        self.ranking = MultiModalRanking()
        self.walk = Walk()
        self.full_route_name = True

    def turn_off_duplicate(self):
        logger.debug("Turning off duplicate in final result.")
        self.metro_object.turn_off_duplicate()
        self.bus_object.turn_off_duplicate()
        self.ranking.turn_off_duplicate()

    def turn_on_duplicate(self):
        logger.debug("Turning on duplicate in final result.")
        self.metro_object.turn_on_duplicate()
        self.bus_object.turn_on_duplicate()
        self.ranking.turn_on_duplicate()

    def get_stops(self, stops_file_path):
        all_stops_df = pd.read_csv(ALL_STOPS_PATH)
        # all_stops_df = all_stops_df[all_stops_df.stop_type == METRO_ENUM]
        all_stops_df = geopandas.GeoDataFrame(
            all_stops_df,
            geometry=geopandas.points_from_xy(
                all_stops_df.stop_lat,
                all_stops_df.stop_lon),
            crs="EPSG:4326"
        )
        return all_stops_df

    def get_color(self, route):
        return self.bus_object.get_color(route)

    @staticmethod
    def custom_sort(x):
        if x >= 0:
            return 0, x
        else:
            return 1, x

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):
        src_type = src.location_type
        src_value = src.location_value

        dst_type = dst.location_type
        dst_value = dst.location_value

        if (src_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM] or
                dst_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM]):
            return []

        nearest_stops_src = [NearestStop(stop_id=src_value, stop_name=src_name, stop_code=src.tkt_code,
                                         stop_type=src_type, geometry='', distance=0, birds_distance=0,
                                         travel_time=0, source_name="")]

        nearest_stops_dst = [
            NearestStop(stop_id=dst_value, stop_name=dst_name, stop_code=dst.tkt_code, stop_type=dst_type,
                        geometry='', distance=0, birds_distance=0, travel_time=0, source_name="")]

        all_src_to_dst_combinations = [
            (src, dst) for dst in nearest_stops_dst for src in nearest_stops_src
            if src != dst and src.stop_id != dst.stop_id
        ]

        unique_src_to_dst_combinations = list(all_src_to_dst_combinations)
        return unique_src_to_dst_combinations

    def get_sorted_on_frequency(self, frequencies, routes, long_names, agency):
        enumerated_list = list(enumerate(frequencies))
        sorted_frequency_list = sorted(enumerated_list, key=lambda x: self.custom_sort(x[1]))
        original_indices = [item[0] for item in sorted_frequency_list]
        sorted_frequency_list = [x[1] for x in sorted_frequency_list]
        sorted_routes_list = [routes[i] for i in original_indices]
        sorted_long_name_list = [long_names[i] for i in original_indices]
        sorted_agency_list = [agency[i] for i in original_indices]
        return sorted_routes_list, sorted_long_name_list, sorted_frequency_list, sorted_agency_list

    def get_route(self, route_section, mode_to_reach_transit):

        (
            route_id,
            vehicle_id,
            departure_time,
            section_type
        ) = route_section.route_id, route_section.vehicle_id, route_section.departure_time, route_section.edge_type

        if section_type == METRO_TYPE_ENUM:
            route = self.metro_object.get_route(route_section, mode_to_reach_transit)
        else:
            route = self.bus_object.get_route(route_section, mode_to_reach_transit)
        return route

    def get_route_fare(self, route):
        try:
            if route[-1].parent_node_stop_type == 'bus':
                if route[0].parent_info is None:
                    return 0
                if route[0].parent_info.get('tkt_code') == route[-1].parent_info.get('tkt_code'):
                    return 0
                try:
                    if route[-1].route_id[0] == -1:
                        return 0
                    if len(route) == 2:
                        return get_bus_fare(route[0].child_info.get('tkt_code'), route[-1].child_info.get('tkt_code'),
                                            route[-1].route_id[0])
                    else:
                        return get_bus_fare(route[0].child_info.get('tkt_code'), route[-1].parent_info.get('tkt_code'),
                                            route[-1].route_id[0])
                except:
                    return 10
        except:
            return 10
        else:
            try:
                return int(route[-1].fare)
            except:
                return 0

    def get_response_type(self, response):
        return self.bus_object.get_response_type(response)

    def get_response(self, request_data):
        mode_to_reach_transit, _ = request_data.get('mode')

        src = request_data.get(SRC)
        dst = request_data.get(DST)
        src_info = src.location_info
        src_cords = (src_info[LAT], src_info[LON])
        dst_info = dst.location_info
        dst_cords = (dst_info[LAT], dst_info[LON])

        time_from_location = request_data.get('time')

        def get_metro_response():
            logger.info("Collecting metro response for Multi-Model")
            metro_response = self.metro_object.get_response(request_data)
            if not metro_response:
                logger.info("Could not find Metro Response.")
                return []
            return metro_response


        def get_self_response():
            logger.info("Collecting self response for Multi-Model")
            responses = []
            start_time = datetime.strptime(time_from_location, '%H:%M:%S')
            direct_walk_duration_from_src_to_dst = self.get_walk_info(src_cords, dst_cords)
            src_to_dst_combinations = self.get_nearest_stops(request_data)

            for (source, destination) in src_to_dst_combinations:
                walk_duration_from_src_to_stop = timedelta(seconds=source.travel_time)  # in hh:mm:ss
                true_start_time_from_location = (start_time + walk_duration_from_src_to_stop).time().strftime(
                    "%H:%M:%S")

                routes = self.algorithms.get_routes(
                    source, destination, true_start_time_from_location, time_from_location, True
                )
                responses.extend(routes)

            responses = [response for response in responses if response is not None]
            if len(responses):
                ranked_responses = self.ranking.rank_result(time_from_location, static_responses_one=responses,
                                                            grouped=True)
                possible_directions_self: list = self.generate_responses(
                    ranked_responses, src, dst, time_from_location, direct_walk_duration_from_src_to_dst,
                    mode_to_reach_transit
                )
            else:
                logger.info("Could not find Self Multi Response.")
                possible_directions_self = []

            return possible_directions_self

        with ThreadPoolExecutor() as executor:
            future_result_1 = executor.submit(get_self_response)
            future_result_2 = executor.submit(get_metro_response)

        possible_directions = future_result_1.result() + future_result_2.result()
        possible_directions = self.sort_on_trip_time(possible_directions)
        return possible_directions if possible_directions else []
