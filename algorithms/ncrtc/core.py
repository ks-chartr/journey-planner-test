from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime
from algorithms.common.core import BaseParent
from algorithms.ncrtc.config import NCRTC_ROUTES_DICT, NCRTC_STOPS_DF
from modules.constants import *
from algorithms.ncrtc.algorithm.core import NCRTCAlgorithms
from algorithms.ncrtc.ranking.core import NCRTCRanking
from models.models import Route, NearestStop
from algorithms.walk.core import Walk
from algorithms.ncrtc.config import NCRTC_STOPS_PATH
import pandas as pd
import geopandas
import copy
from algorithms.bus.core import Bus
from algorithms.metro.core import Metro
from algorithms.multimodal.core import MultiModal
from modules.decorators import cache_data
from modules.nearest_cluster import get_centroids_given_location
from modules.logger import logger
from models.models import NCRTCRouteSection


class NCRTC(BaseParent):
    def __init__(self):
        super().__init__()
        self.mode = NCRTC_ENUM
        self.stop_type = NCRTC_TYPE_ENUM
        self.stops_index_offset = NCRTC_STOP_INDEX_OFFSET

        self.routes_dict = NCRTC_ROUTES_DICT
        self.stops = self.get_stops(NCRTC_STOPS_PATH)
        self.gtfs_stops = NCRTC_STOPS_DF

        self.algorithms: NCRTCAlgorithms = NCRTCAlgorithms()
        self.ranking: NCRTCRanking = NCRTCRanking()
        self.bus_object = Bus()
        self.metro_object = Metro()
        self.metro_object.algorithms.route_section = NCRTCRouteSection
        self.multi_object = MultiModal()
        self.walk = Walk()

        self.src_location_search_count = NCRTC_SRC_LOCATIONS_SEARCH_COUNT
        self.dst_location_search_count = NCRTC_DST_LOCATIONS_SEARCH_COUNT


    @cache_data('ncrtc_stops_csv_file_2')
    def get_stops(self, stops_file_path):
        stops_ncrtc = pd.read_csv(stops_file_path)
        stops_ncrtc = geopandas.GeoDataFrame(
            stops_ncrtc,
            geometry=geopandas.points_from_xy(stops_ncrtc.stop_lat, stops_ncrtc.stop_lon),
            crs="EPSG:4326"
        )
        return stops_ncrtc

    @cache_data('ncrtc_stops_json')
    def get_stops_json(self):
        stops_ncrtc = pd.read_csv(NCRTC_STOPS_PATH)
        stops_ncrtc = stops_ncrtc[['stop_id', 'stop_lat', 'stop_lon', 'stop_name']]
        stops_ncrtc.rename(columns={'stop_name': 'name', 'stop_lat': 'lat', 'stop_lon': 'lng', 'stop_id': 'id'},
                           inplace=True)
        stops_ncrtc['stop_type'] = self.mode

        stop_list = stops_ncrtc.to_dict('records')
        stop_list = sorted(stop_list, key=lambda x: x['id'])
        return stop_list

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):
        logger.debug(f"Getting src dst air for walk for NCRTC")
        logger.debug(
            f"src:{src},src name:{src_name},src cords:{src_cords},dst:{dst},dst name:{dst_name},dst cords:{dst_cords}"
        )
        if (src.location_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM, NCRTC_TYPE_ENUM] or
                dst.location_type not in [BUS_TYPE_ENUM, METRO_TYPE_ENUM, NCRTC_TYPE_ENUM]):
            return []

        if src.location_type != NCRTC_TYPE_ENUM:
            nearest_stops_src = get_centroids_given_location(src_cords, self.src_location_search_count, self)
        else:
            nearest_stops_src = [
                NearestStop(stop_id=src.location_value, stop_name=src_name, stop_code=src.tkt_code,
                            stop_type=src.location_type, geometry='', distance=0, birds_distance=0, travel_time=0,
                            source_name="")
            ]

        if dst.location_type != NCRTC_TYPE_ENUM:
            nearest_stops_dst = get_centroids_given_location(dst_cords, self.dst_location_search_count, self)
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

        if route_id == [-1]:
            route = self.walk.get_route(route_section, mode_to_reach_transit)

        else:
            route = Route()
            route_id = route_id[0]

            val = self.routes_dict[route_id]
            route.route = val[1].split('_')[0]
            route.routes = [val[1].split('_')[0]]
            route.agency = "NCRTC"
            route.frequency = -1
            route.long_name = f" towards {val[1].split(' to ')[1]}"

            route.type = NCRTC_ENUM
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
            logger.info("Collecting self response for Ncrtc.")
            responses = []
            start_time = datetime.strptime(time_from_location, '%H:%M:%S')
            direct_walk_duration_from_src_to_dst = self.get_walk_info(src_cords, dst_cords)
            src_to_dst_combinations = self.get_nearest_stops(request_data)

            for (source, destination) in src_to_dst_combinations:
                walk_duration_from_src_to_stop = timedelta(seconds=source.travel_time)  # in dd:hh:mm:ss
                true_start_time_from_stop = (start_time + walk_duration_from_src_to_stop).time().strftime("%H:%M:%S")
                routes = self.algorithms.get_routes(source, destination, true_start_time_from_stop, time_from_location)
                responses.extend(routes)

            if len(responses):
                responses = [response for response in responses if response is not None]

                ranked_responses = self.ranking.rank_result(time_from_location, static_responses_one=responses, grouped=True)
                possible_directions_self: list = self.generate_responses(
                    ranked_responses, src, dst, time_from_location, direct_walk_duration_from_src_to_dst,
                    mode_to_reach_transit
                )

            else:
                logger.info("Could not find Self Ncrtc Response.")
                possible_directions_self = []

            return possible_directions_self


        possible_directions = get_self_response()
        possible_directions = self.sort_on_trip_time(possible_directions)
        return possible_directions if possible_directions else []
