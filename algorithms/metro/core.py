from datetime import datetime, timedelta

import geopandas
import pandas as pd

from algorithms.common.core import BaseParent
from algorithms.metro.algorithm.core import MetroAlgorithms
from algorithms.metro.config import METRO_ROUTES_DICT, METRO_STOPS_DF
from algorithms.metro.config import METRO_STOPS_PATH
from algorithms.metro.ranking.core import MetroRanking
from algorithms.walk.core import Walk
from models.models import NearestStop
from models.models import Route
from modules.constants import *
from modules.decorators import cache_data
from modules.logger import logger
from modules.miscellaneous import get_frequency


class Metro(BaseParent):
    def __init__(self):
        super().__init__()
        self.mode = METRO_ENUM
        self.stop_type = METRO_TYPE_ENUM
        self.stops_index_offset = METRO_STOP_INDEX_OFFSET

        self.routes_dict = METRO_ROUTES_DICT
        self.stops = self.get_stops(METRO_STOPS_PATH)
        self.gtfs_stops = METRO_STOPS_DF

        self.algorithms: MetroAlgorithms = MetroAlgorithms()
        self.ranking: MetroRanking = MetroRanking()
        self.walk = Walk()

        self.src_location_search_count = METRO_SRC_LOCATIONS_SEARCH_COUNT
        self.dst_location_search_count = METRO_DST_LOCATIONS_SEARCH_COUNT

    def turn_off_duplicate(self):
        logger.debug("Turning off duplicate in final result.")
        self.ranking.turn_off_duplicate()

    def turn_on_duplicate(self):
        logger.debug("Turning on duplicate in final result.")
        self.ranking.turn_on_duplicate()

    @cache_data('metro_stops_csv_file')
    def get_stops(self, stops_file_path):
        stops_metro = pd.read_csv(stops_file_path)
        stops_metro = geopandas.GeoDataFrame(
            stops_metro,
            geometry=geopandas.points_from_xy(stops_metro.stop_lat, stops_metro.stop_lon),
            crs="EPSG:4326"
        )
        return stops_metro

    @cache_data('metro_stops_json')
    def get_stops_json(self):
        stops_metro = pd.read_csv(METRO_STOPS_PATH)
        stops_metro = stops_metro[['stop_id', 'stop_lat', 'stop_lon', 'stop_name']]
        stops_metro.rename(columns={'stop_name': 'name', 'stop_lat': 'lat', 'stop_lon': 'lng', 'stop_id': 'id'},
                           inplace=True)
        stops_metro['stop_type'] = self.mode

        stop_list = stops_metro.to_dict('records')
        stop_list = sorted(stop_list, key=lambda x: x['id'])
        return stop_list

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):

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
            departure_time
        ) = route_section.route_id, route_section.vehicle_id, route_section.departure_time

        if route_id in [-1, -50]:
            route = self.walk.get_route(route_section, mode_to_reach_transit)

        else:
            route = Route()
            route_id = route_id[0]

            val = self.routes_dict[route_id]
            route.route = val[1].split('_')[0]
            route.routes = [val[1].split('_')[0]]
            route.agency = "DMRC"
            route.frequency = get_frequency(route_id, departure_time)
            route.long_name = f" towards {val[1].split(' to ')[1]}"

            route.type = METRO_ENUM
            route.short_name = val[0]
            route.vehicle_id = ''
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


    def get_route_fare(self, route):
        try:
            fare = float(route[-1].fare)
        except Exception as e:
            logger.error(f"KeyError: {e}")
            fare = 0
        return fare

    def get_response_type(self, response):
        return 'static'

    def get_response(self, request_data):
        mode_to_reach_transit, _ = request_data.get('mode')

        src = request_data.get(SRC)
        dst = request_data.get(DST)
        src_info = src.location_info
        src_cords = (src_info[LAT], src_info[LON])
        dst_info = dst.location_info
        dst_cords = (dst_info[LAT], dst_info[LON])

        time_from_location = request_data.get('time')

        def get_self_response():
            logger.info("Collecting self response for Metro.")
            responses = []
            start_time = datetime.strptime(time_from_location, '%H:%M:%S')
            direct_walk_duration_from_src_to_dst = self.get_walk_info(src_cords, dst_cords)
            src_to_dst_combinations = self.get_nearest_stops(request_data)

            # t1 = tmm.time_from_location()
            for (source, destination) in src_to_dst_combinations:
                walk_duration_from_src_to_stop = timedelta(seconds=source.travel_time)  # in dd:hh:mm:ss
                true_start_time_from_stop = (start_time + walk_duration_from_src_to_stop).time().strftime("%H:%M:%S")
                routes = self.algorithms.get_routes(source, destination, true_start_time_from_stop, time_from_location)
                responses.extend(routes)

            if len(responses):
                responses = [response for response in responses if response is not None]

                ranked_responses = self.ranking.rank_result(time_from_location, static_responses_one=responses,
                                                            grouped=True)
                possible_directions_self: list = self.generate_responses(
                    ranked_responses, src, dst, time_from_location, direct_walk_duration_from_src_to_dst,
                    mode_to_reach_transit
                )

            else:
                logger.info("Could not find Self Metro Response.")
                possible_directions_self = []

            return possible_directions_self

        possible_directions = get_self_response()
        possible_directions = self.sort_on_trip_time(possible_directions)

        return possible_directions if possible_directions else []
