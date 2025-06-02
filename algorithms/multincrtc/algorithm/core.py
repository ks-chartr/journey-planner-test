"""
This module contains the core algorithms for NCRTC.
"""

from modules.logger import logger
import json
from algorithms.metro.algorithm.core import MetroAlgorithms
from algorithms.bus.algorithm.core import BusAlgorithms
from algorithms.multimodal.algorithm.core import MultiModalAlgorithms
from algorithms.ncrtc.algorithm.core import NCRTCAlgorithms
from algorithms.common.algorithm.core import BaseAlgorithms
from algorithms.ncrtc.config import NCRTC_SCHEDULE_DB_PATH, NCRTC_RESPONSE_DB_PATH
from modules.constants import *
from models.models import NCRTCRouteSection
from models.models import Location
from modules.miscellaneous import haversine_distance
from modules.nearest_cluster import get_centroids_given_location
from models.models import WalkRouteSection, RouteSection, NearestStop
import copy


class MultiNCRTCAlgorithms(BaseAlgorithms):
    """
    Class to implement the core algorithms for NCRTC.
    """

    def __init__(self):
        """
        Constructor for NCRTCAlgorithms.
        """
        super().__init__()
        self.schedule_connection = self.connectDB(NCRTC_SCHEDULE_DB_PATH)
        self.response_connection = self.connectDB(NCRTC_RESPONSE_DB_PATH)
        self.response_table_name = 'metro_response'
        self.route_section = NCRTCRouteSection
        self.mode = NCRTC_ENUM
        self.MAX_DAY_TIME = '23:59:59'
        self.metro_fare = []
        self.leg_transfer_time = NCRTC_LEG_TRANSFER_TIME
        self.index_offset = NCRTC_STOP_INDEX_OFFSET
        self.allowed_legs = MAXIMUM_LEGS_ALLOWED_NCRTC

        self.metro_algorithms = MetroAlgorithms()
        self.bus_algorithms = BusAlgorithms()
        self.ncrtc_algorithms = NCRTCAlgorithms()

        self.transit_object = None

    def get_dept_time(self, route_section, dept_time, init=True):
        edge_type = route_section.edge_type

        if edge_type == BUS_TYPE_ENUM:
            dept_time = self.bus_algorithms.get_dept_time(route_section, dept_time, init)
        elif edge_type == METRO_TYPE_ENUM:
            dept_time = self.metro_algorithms.get_dept_time(route_section, dept_time, init)
        elif edge_type == NCRTC_ENUM:
            dept_time = self.ncrtc_algorithms.get_dept_time(route_section, dept_time, init)

        return dept_time

    def evaluate_parent_child_node_info(self, routes):
        for route in routes:
            for route_section in route:
                if route_section.edge_type == WALK_TYPE_ENUM:
                    route_section.child_info = Location(
                        route_section.child_node, route_section.child_node_stop_type
                    ).location_info

                    route_section.parent_info = Location(
                        route_section.parent_node, route_section.parent_node_stop_type
                    ).location_info
                else:
                    route_section.child_info = Location(
                        route_section.child_node, route_section.edge_type
                    ).location_info

                    route_section.parent_info = Location(
                        route_section.parent_node, route_section.edge_type
                    ).location_info
        return routes

    def get_initial_walk_edge(self, src, src_new, time_at_src):

        first_route_section = WalkRouteSection()
        first_route_section.child_node = src.stop_id
        first_route_section.child_node_stop_type = src.stop_type
        first_route_section.parent_node = src.stop_id
        first_route_section.parent_node_stop_type = src.stop_type
        first_route_section.route_id = None
        first_route_section.departure_time = time_at_src
        first_route_section.arrival_time = time_at_src
        first_route_section.edge_type = WALK_ENUM
        first_route_section.travel_time_of_edge = 0

        second_route_section = WalkRouteSection()
        second_route_section.child_node = src_new.stop_id
        second_route_section.child_node_stop_type = src_new.stop_type
        second_route_section.parent_node = src.stop_id
        second_route_section.parent_node_stop_type = src.stop_type
        second_route_section.route_id = [-1]
        second_route_section.travel_time_of_edge = src_new.travel_time
        second_route_section.edge_type = WALK_TYPE_ENUM
        second_route_section.departure_time = time_at_src
        second_route_section.arrival_time = self.convAdd(time_at_src, src_new.travel_time)
        second_route_section.distance = src_new.distance
        second_route_section.birds_distance = src_new.birds_distance

        return [[first_route_section, second_route_section]]

    def add_last_walk_edge(self, src_type_of_walk_edge, dst_of_walk_edge, routes, dist_containing_stops):

        final_routes = []
        stop_id_dict = {
            (
                stop.stop_id if stop.stop_id < self.index_offsets[stop.stop_type]
                else stop.stop_id - self.index_offsets[stop.stop_type]
            ): stop for stop in dist_containing_stops
        }

        for dst in dst_of_walk_edge:
            for route in routes:
                walk_route = WalkRouteSection()
                walk_route.child_node = dst.stop_id if dst.stop_id < self.index_offsets[dst.stop_type] else dst.stop_id - self.index_offsets[dst.stop_type]
                walk_route.parent_node = route[-1].child_node
                walk_route.route_id = [-1]
                try:
                    walk_distance_of_transfer = stop_id_dict[walk_route.parent_node].distance
                except KeyError:
                    walk_distance_of_transfer = stop_id_dict[walk_route.child_node].distance

                walk_time_of_transfer = int(walk_distance_of_transfer * 1000 / WALKING_SPEED)
                walk_route.travel_time_of_edge = walk_time_of_transfer
                walk_route.arrival_time = self.convAdd(route[-1].arrival_time, walk_route.travel_time_of_edge)
                walk_route.child_node_stop_type = dst.stop_type
                walk_route.parent_node_stop_type = src_type_of_walk_edge
                walk_route.edge_type = WALK_TYPE_ENUM
                walk_route.distance = walk_distance_of_transfer
                walk_route.birds_distance = walk_distance_of_transfer
                final_routes.append(route + [walk_route])

        return final_routes

    def get_transit_edge_routes(self, nearest_stops_edge_src: list, nearest_stops_edge_dst: list,
                                time_from_stop, add_initial_walk=False):
        all_src_to_dst_combinations = [
            (src, dst) for dst in nearest_stops_edge_dst for src in nearest_stops_edge_src
            if src != dst and src.stop_id != dst.stop_id
        ]
        unique_src_to_dst_combinations = list(all_src_to_dst_combinations)

        routes = []
        for src, dst in unique_src_to_dst_combinations:
            if self.transit_object.mode == BUS_ENUM:
                (
                    static_zero_hop_route,
                    static_one_hop_route
                ) = self.transit_object.algorithms.get_routes(src, dst, time_from_stop, None, False)
                routes_list = static_zero_hop_route + static_one_hop_route
            else:
                routes_list = self.transit_object.algorithms.get_routes(src, dst, time_from_stop, None, False)

            routes.extend(routes_list)

        return routes

    def get_multi_ncrtc_routes(self, src, src_location, src_ncrtc, dst_ncrtc, dst, dst_location, time_from_stop):
        src_ncrtc_cords = Location(src_ncrtc.stop_id, src_ncrtc.stop_type, src_ncrtc.stop_name).cords
        dst_ncrtc_cords = Location(dst_ncrtc.stop_id, dst_ncrtc.stop_type, dst_ncrtc.stop_name).cords

        src_cords, dst_cords = src_location.cords, dst_location.cords

        if src != src_ncrtc:
            if haversine_distance(
                    src_ncrtc_cords[0], src_ncrtc_cords[1], src_cords[0], src_cords[1]
            ) > MAXIMUM_WALK_DISTANCE_to_REACH_NCRTC:
                nearest_stops_of_transit_by_ncrtc_src = get_centroids_given_location(
                                                                                src_ncrtc_cords,
                                                                                TRANSIT_LOCATION_SEARCH_COUNT_BY_NCRTC,
                                                                                self.transit_object)
                if (
                        (self.transit_object.mode == MULTI_ENUM and src.stop_type in [BUS_ENUM, METRO_ENUM])
                        or (src.stop_type == self.transit_object.stop_type)
                ):
                    src_locations = [src]
                else:
                    src_locations = self.get_nearest_stops_from_location(
                        src_location.location_value, src_location.location_type, self.transit_object.stop_type,
                        src.stop_name, src_location.tkt_code
                    )

                all_src_side_routes = self.get_transit_edge_routes(src_locations,
                                                                   nearest_stops_of_transit_by_ncrtc_src,
                                                                   time_from_stop)
                all_src_side_routes = self.add_last_walk_edge(src.stop_type,
                                                              [src_ncrtc],
                                                              all_src_side_routes,
                                                              nearest_stops_of_transit_by_ncrtc_src)
                if not all_src_side_routes:
                    return []
            else:
                all_src_side_routes = self.get_initial_walk_edge(src, src_ncrtc, time_from_stop)
        else:
            all_src_side_routes = []

        intermediary_to_ncrtc_dst_routes = []
        if all_src_side_routes:
            for src_side_route in all_src_side_routes:

                if src_side_route[-1].edge_type == WALK_TYPE_ENUM and src_side_route[-2].edge_type == WALK_TYPE_ENUM:
                    src_side_route[-2].child_node = src_side_route[-1].child_node
                    src_side_route[-2].child_info = src_side_route[-1].child_info
                    src_side_route[-2].child_node_stop_type = src_side_route[-1].child_node_stop_type
                    src_side_route[-2].travel_time_of_edge += src_side_route[-1].travel_time_of_edge
                    src_side_route[-2].arrival_time = self.convAdd(src_side_route[-2].arrival_time,
                                                                   src_side_route[-2].travel_time_of_edge)
                    src_side_route[-2].distance += src_side_route[-1].distance
                    src_side_route[-2].birds_distance += src_side_route[-1].birds_distance
                    src_side_route = src_side_route[:-1]

                time_at_src_ncrtc = self.convAdd(src_side_route[-1].arrival_time, NCRTC_WAITING_TIME_PENALTY)
                ncrtc_routes = self.ncrtc_algorithms.get_routes(
                    src_ncrtc, dst_ncrtc, time_at_src_ncrtc, None, False
                )

                for ncrtc_route in ncrtc_routes:
                    route_till_ncrtc_dst = src_side_route + ncrtc_route[1:]
                    intermediary_to_ncrtc_dst_routes.append(route_till_ncrtc_dst)
        else:
            time_at_src_ncrtc = time_from_stop
            intermediary_to_ncrtc_dst_routes = self.ncrtc_algorithms.get_routes(src_ncrtc, dst_ncrtc, time_at_src_ncrtc,
                                                                                None, False)

        final_routes = []

        if dst != dst_ncrtc:
            if haversine_distance(
                    dst_ncrtc_cords[0], dst_ncrtc_cords[1], dst_cords[0], dst_cords[1]
            ) > MAXIMUM_WALK_DISTANCE_to_REACH_NCRTC:
                nearest_stops_of_transit_by_ncrtc_dst = get_centroids_given_location(
                                                                            dst_ncrtc_cords,
                                                                            TRANSIT_LOCATION_SEARCH_COUNT_BY_NCRTC,
                                                                            self.transit_object)
                intermediary_to_ncrtc_dst_routes = self.add_last_walk_edge(dst_ncrtc.stop_type,
                                                                           nearest_stops_of_transit_by_ncrtc_dst,
                                                                           intermediary_to_ncrtc_dst_routes,
                                                                           nearest_stops_of_transit_by_ncrtc_dst)
                if self.transit_object.mode == 'multi' or dst.stop_type == self.transit_object.stop_type: #TODO: Check validity
                    dst_locations = [dst]
                else:
                    dst_locations = self.get_nearest_stops_from_location(
                        dst_location.location_value, dst_location.location_type, self.transit_object.stop_type,
                        dst.stop_name, dst_location.tkt_code
                    )

                all_dst_side_routes = self.get_transit_edge_routes(nearest_stops_of_transit_by_ncrtc_dst,
                                                                   dst_locations, time_from_stop, True)
                for intermediary_route in intermediary_to_ncrtc_dst_routes:
                    for dst_side_route in all_dst_side_routes:
                        if (
                                intermediary_route[-1].edge_type == WALK_TYPE_ENUM and
                                dst_side_route[1].edge_type == WALK_TYPE_ENUM
                        ):
                            intermediary_route[-1].child_node = dst_side_route[1].child_node
                            intermediary_route[-1].child_info = dst_side_route[1].child_info
                            intermediary_route[-1].child_node_stop_type = dst_side_route[1].child_node_stop_type
                            intermediary_route[-1].travel_time_of_edge += dst_side_route[1].travel_time_of_edge
                            intermediary_route[-1].arrival_time = self.convAdd(
                                intermediary_route[-1].arrival_time,
                                intermediary_route[-1].travel_time_of_edge
                            )
                            intermediary_route[-1].distance += dst_side_route[1].distance
                            intermediary_route[-1].birds_distance += dst_side_route[1].birds_distance

                            final_routes.append(intermediary_route + dst_side_route[2:])
                        else:
                            final_routes.append(intermediary_route + dst_side_route[1:])

            else:
                final_routes = self.add_last_walk_edge(dst_ncrtc, [dst], intermediary_to_ncrtc_dst_routes, [dst])
        else:
            final_routes = intermediary_to_ncrtc_dst_routes

        return final_routes

    @staticmethod
    def get_src_dst_ncrtc_combinations(src, src_cords, dst, dst_cords, **kwargs):
        ncrtc_object = kwargs["self_ncrtc"]

        if src.stop_type == NCRTC_TYPE_ENUM:
            ncrtc_stops_src = [src]
        else:
            ncrtc_stops_src = get_centroids_given_location(src_cords, NCRTC_LOCATION_SEARCH_COUNT, ncrtc_object)

        if dst.stop_type == NCRTC_TYPE_ENUM:
            ncrtc_stops_dst = [dst]
        else:
            ncrtc_stops_dst = get_centroids_given_location(dst_cords, NCRTC_LOCATION_SEARCH_COUNT, ncrtc_object)

        all_src_to_dst_combinations = [
            (src, dst) for dst in ncrtc_stops_dst for src in ncrtc_stops_src
            if src != dst and src.stop_id != dst.stop_id
        ]
        unique_src_to_dst_combinations = list(all_src_to_dst_combinations)
        return unique_src_to_dst_combinations
    
    @staticmethod
    def get_src_dst_ids_for_ncrtc(src, src_cords, dst, dst_cords, **kwargs):
        ncrtc_object = kwargs["self_ncrtc"]

        if src.stop_type == NCRTC_TYPE_ENUM:
            ncrtc_stops_src = [src]
        else:
            ncrtc_stops_src = get_centroids_given_location(src_cords, NCRTC_LOCATION_SEARCH_COUNT, ncrtc_object)

        if dst.stop_type == NCRTC_TYPE_ENUM:
            ncrtc_stops_dst = [dst]
        else:
            ncrtc_stops_dst = get_centroids_given_location(dst_cords, NCRTC_LOCATION_SEARCH_COUNT, ncrtc_object)

        src_stop_ids = [stop.stop_id for stop in ncrtc_stops_src]
        dst_stop_ids = [stop.stop_id for stop in ncrtc_stops_dst]

        return src_stop_ids, dst_stop_ids


    def get_routes(self, src, dst, time_from_stop, time_from_location, modify_route=True, **kwargs):
        ncrtc_object = kwargs["self_ncrtc"]
        transit_object = kwargs["self_transit"]
        self.transit_object = transit_object

        src_location = Location(src.stop_id, src.stop_type, src.stop_name)
        dst_location = Location(dst.stop_id, dst.stop_type, dst.stop_name)

        src_to_dst_combinations_ncrtc = self.get_src_dst_ncrtc_combinations(src, src_location.cords,
                                                                            dst, dst_location.cords,
                                                                            self_ncrtc=ncrtc_object)
        all_routes = []
        for (src_ncrtc, dst_ncrtc) in src_to_dst_combinations_ncrtc:
            transit_ncrtc_routes = self.get_multi_ncrtc_routes(src, src_location, src_ncrtc, dst_ncrtc, dst,
                                                               dst_location, time_from_stop)
            all_routes.extend(transit_ncrtc_routes)

        all_routes = [self.add_schedule(route, self.allowed_legs) for route in all_routes]
        all_routes = self.evaluate_parent_child_node_info(all_routes)

        if not modify_route:
            return all_routes

        modified_routes = []
        for route in all_routes:
            if not route:
                continue

            new_route = [copy.copy(rt) for rt in route]
            new_route = self.modify_route(src, dst, new_route, time_from_location, RouteSection)
            new_route[0].route_id = None
            modified_routes.append(new_route)

        return modified_routes
