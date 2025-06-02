from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime

from algorithms.common.core import BaseParent
from modules.constants import *
from algorithms.multincrtc.algorithm.core import MultiNCRTCAlgorithms
from algorithms.multincrtc.ranking.core import MultiNCRTCRanking
from models.models import Route, NearestStop
from algorithms.walk.core import Walk
from algorithms.metro.core import Metro
from algorithms.bus.core import Bus
from algorithms.multimodal.core import MultiModal
from algorithms.ncrtc.core import NCRTC
# PTX import removed
from modules.logger import logger
from modules.nearest_cluster import get_centroids_given_location
import copy
from serializers.utils import is_in_location


class MultiNCRTC(BaseParent):
    def __init__(self):
        super().__init__()
        # PTX object removed
        self.algorithms: MultiNCRTCAlgorithms = MultiNCRTCAlgorithms()
        self.ranking: MultiNCRTCRanking = MultiNCRTCRanking()
        self.transit_object = None
        self.ncrtc_object = NCRTC()
        self.walk = Walk()

        self.src_location_search_count = NCRTC_SRC_LOCATIONS_SEARCH_COUNT
        self.dst_location_search_count = NCRTC_DST_LOCATIONS_SEARCH_COUNT

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):

        logger.debug(f"Getting src dst air for walk for NCRTC Metro Combination.")
        logger.debug(
            f"src:{src},src name:{src_name},src cords:{src_cords},dst:{dst},dst name:{dst_name},dst cords:{dst_cords}"
        )
        nearest_stops_src = [
                NearestStop(stop_id=src.location_value, stop_name=src_name, stop_code=src.tkt_code,
                            stop_type=src.location_type, geometry='', distance=0, birds_distance=0, travel_time=0,
                            source_name="")
            ]

        nearest_stops_dst = [
                NearestStop(stop_id=dst.location_value, stop_name=dst_name, stop_code=dst.tkt_code,
                            stop_type=dst.location_type, geometry='', distance=0, birds_distance=0, travel_time=0,
                            source_name="")
            ]

        all_src_to_dst_combinations = [
            (src, dst) for dst in nearest_stops_dst for src in nearest_stops_src
            if src != dst and src.stop_id != dst.stop_id
        ]
        unique_src_to_dst_combinations = list(all_src_to_dst_combinations)
        return unique_src_to_dst_combinations

    def get_color(self, route):
        color_dict = COLOR_DICT
        return '#000000' if route.route.lower() not in color_dict else color_dict[route.route.lower()]

    def get_route(self, route_section, mode_to_reach_transit):
        (
            route_id,
            vehicle_id,
            departure_time,
            section_type
        ) = route_section.route_id, route_section.vehicle_id, route_section.departure_time, route_section.edge_type

        if section_type == METRO_TYPE_ENUM:
            route = Metro().get_route(route_section, mode_to_reach_transit)
        elif section_type == BUS_TYPE_ENUM:
            route = Bus().get_route(route_section, mode_to_reach_transit)
        elif section_type == MULTI_ENUM:
            route = MultiModal().get_route(route_section, mode_to_reach_transit)
        elif section_type == NCRTC_TYPE_ENUM:
            route = NCRTC().get_route(route_section, mode_to_reach_transit)
        elif section_type == WALK_TYPE_ENUM:
            route = NCRTC().get_route(route_section, mode_to_reach_transit)
        else:
            raise ValueError('Passed route_section is not a valid case.')

        return route

    def get_route_fare(self, route):
        try:
            fare = float(route[-1].fare)
        except Exception as e:
            fare = 0
        return fare

    def get_response_type(self, response):
        return 'static'

    def assign_transit_object(self, mode_of_transit):
        if BUS_ENUM in mode_of_transit:
            self.transit_object = Bus()

        elif METRO_ENUM in mode_of_transit:
            self.transit_object = Metro()

        elif MULTI_ENUM in mode_of_transit:
            self.transit_object = MultiModal()
        else:
            logger.error(f"{mode_of_transit} is not a valid mode.")
            raise ValueError(f"{mode_of_transit} is not a valid mode.")

    def get_response(self, request_data):
        mode_to_reach_transit, mode_of_transit = request_data.get('mode')
        self.assign_transit_object(mode_of_transit)

        src = request_data.get(SRC)
        dst = request_data.get(DST)
        src_info = src.location_info
        src_cords = (src_info[LAT], src_info[LON])
        dst_info = dst.location_info
        dst_cords = (dst_info[LAT], dst_info[LON])

        time_from_location = request_data.get('time')

        # PTX mode is not implemented

        def get_ptx_auto_response():
            logger.warning("get_ptx_auto_response not implemented")
            return []

        def get_self_response():
            logger.info("Collecting Self response for Multi Ncrtc")
            responses = []
            start_time = datetime.strptime(time_from_location, '%H:%M:%S')
            direct_walk_duration_from_src_to_dst = self.get_walk_info(src_cords, dst_cords)
            src_to_dst_combinations = self.get_nearest_stops(request_data)

            for (source, destination) in src_to_dst_combinations:
                walk_duration_from_src_to_stop = timedelta(seconds=source.travel_time)  # in dd:hh:mm:ss
                true_start_time_from_stop = (start_time + walk_duration_from_src_to_stop).time().strftime("%H:%M:%S")
                routes = self.algorithms.get_routes(source, destination, true_start_time_from_stop, time_from_location,
                                                    self_ncrtc=self.ncrtc_object, self_transit=self.transit_object)
                responses.extend(routes)

            if len(responses):
                responses = [response for response in responses if response is not None]

                ranked_responses = self.ranking.rank_result(time_from_location, static_responses_one=responses, grouped=True)
                possible_directions_self: list = self.generate_responses(
                    ranked_responses, src, dst, time_from_location, direct_walk_duration_from_src_to_dst, mode_to_reach_transit
                )
            else:
                logger.error("Could not find Self Multi Ncrtc Response.")
                possible_directions_self = []

            return possible_directions_self

        # Only run self response, PTX is not implemented
        possible_directions = get_self_response()
        possible_directions = self.sort_on_trip_time(possible_directions)

        return possible_directions if possible_directions else []
