# Description: This file contains the core logic of the bus algorithm.
import copy
import itertools
import json
from functools import lru_cache
from typing import List

import networkx as nx

from algorithms.bus.config import CLUSTER_DETAILS
from algorithms.bus.config import ROUTE_STOP_DICT
from algorithms.bus.config import ZERO_HOP_DB_PATH, BUS_TIME_TABLE_DETAILS_DB_PATH, BUS_SCHEDULE_DB_PATH, BUS_GRAPH
from algorithms.common.algorithm.core import BaseAlgorithms
from algorithms.walk.algorithm.core import WalkingAlgorithm
from models.models import BusRouteSection, NearestStop, Location
from modules.constants import *
from modules.logger import logger


class BusAlgorithms(BaseAlgorithms):

    def __init__(self):
        super().__init__()
        self.allow_one_hop = True
        self.allow_zero_hop = True
        self.mode = BUS_ENUM

        self.zero_hop_conn = self.connectDB(ZERO_HOP_DB_PATH, return_dict=True)
        self.bus_time_table_details_conn = self.connectDB(BUS_TIME_TABLE_DETAILS_DB_PATH, return_dict=True)
        self.schedule_connection = self.connectDB(BUS_SCHEDULE_DB_PATH)

        self.cluster_details = self.get_cluster_details(CLUSTER_DETAILS)
        self.walking_mode = WalkingAlgorithm()

    @staticmethod
    def get_cluster_details(cluster_details_dict):
        cluster_details = {}
        for key, values in cluster_details_dict.items():
            for value in values:
                cluster_details[value] = key
        del cluster_details_dict
        return cluster_details

    def turn_off_one_hop(self):
        logger.debug("Turning off one hop in final result.")
        self.allow_one_hop = False

    def turn_off_zero_hop(self):
        logger.debug("Turning off zero hop in final result.")
        self.allow_zero_hop = False

    def get_dept_time(self, route_section, dept_time, init=True):
        stop_id = route_section.parent_node
        route_id = route_section.route_id

        if not self.compare_elements(route_id, [-1]):
            return dept_time

        if len(route_id) == 1:
            route_id = f"('{route_id[0]}')"
        else:
            route_id = tuple(route_id)

        query = f"""select min(departure_time) from bus_schedule 
                            where stop_id is {stop_id} and route_id in {route_id} 
                            and departure_time > '{dept_time}'"""

        departure_time = self.fetch_result(self.schedule_connection, query)[0][0]

        if departure_time is None or self.get_waiting_time(dept_time, departure_time) > WAITING_TIME_THRESHOLD:
            return None

        return departure_time

    def evaluate_parent_child_node_info(self, routes):
        for route in routes:
            for route_section in route:
                try:
                    route_section.child_info = Location(route_section.child_node, self.mode).location_info
                    route_section.parent_info = Location(route_section.parent_node, self.mode).location_info
                except AttributeError:
                    logger.debug("Could not add child parent info for:", route_section)
        return routes

    @lru_cache(maxsize=500)
    def get_tt(self, src_id, dst_id, route_id):
        tt_details_from_src_to_dst = f'SELECT TRAVEL_TIME FROM TT_DETAILS WHERE SRC IS {src_id} AND DEST IS {dst_id} AND ROUTE_ID IS {route_id}'
        time_detail = self.fetch_result(self.bus_time_table_details_conn, tt_details_from_src_to_dst)[0][0]
        return time_detail

    def get_route_section_list(self, stop_ids, route_ids, src_id, dst_id, route_id):
        route_sections = []
        for i in range(1, len(stop_ids)):
            route_section = BusRouteSection()
            route_section.child_node = stop_ids[i]
            route_section.parent_node = stop_ids[i - 1]
            route_section.route_id = route_ids
            route_sections.append(route_section)

            route_section.parent_info = Location(route_section.parent_node, route_section.stop_type).location_info
            route_section.child_info = Location(route_section.child_node, route_section.stop_type).location_info

        last_route_section = route_sections[-1]
        last_route_section.travel_time_of_edge = self.get_tt(src_id, dst_id, route_id)

        return route_sections

    def get_route(self, src, dst, route_data, time):
        """
        args:
            src: NearestStop
            dst: NearestStop
            route_data: List[List]
            time: str
        return:
            List[BusRouteSection]
        """

        src_id = src.stop_id if isinstance(src, NearestStop) else src
        dst_id = dst.stop_id if isinstance(dst, NearestStop) else dst

        _route_ids_index = 0
        _src_id_index = 1
        _dst_id_index = 2

        if src_id == dst_id:
            return []

        route_ids = route_data[_route_ids_index]
        pruned_route_ids = route_ids

        if len(pruned_route_ids):
            route_data[_route_ids_index] = pruned_route_ids

        src_id_after_walk = route_data[_src_id_index]
        dst_id_before_walk = route_data[_dst_id_index]
        route_ids_from_src_to_dst = route_data[_route_ids_index]

        first_route_id = route_ids_from_src_to_dst[0]
        index_src_stop_id_after_walk = ROUTE_STOP_DICT[first_route_id].index(src_id_after_walk)
        index_dst_stop_id_after_walk = ROUTE_STOP_DICT[first_route_id].index(dst_id_before_walk)

        route_sections_list = []
        if index_src_stop_id_after_walk < index_dst_stop_id_after_walk:
            stop_ids_for_route_id = tuple(
                ROUTE_STOP_DICT[first_route_id][index_src_stop_id_after_walk: index_dst_stop_id_after_walk + 1]
            )
            route_sections_list = self.get_route_section_list(stop_ids_for_route_id, route_ids_from_src_to_dst,
                                                              src_id_after_walk, dst_id_before_walk, first_route_id)

        if not route_sections_list:
            return []

        start_route_section = BusRouteSection()
        start_route_section.child_node = src_id
        start_route_section.parent_node = src_id
        start_route_section.arrival_time = time
        start_route_section.departure_time = time
        start_route_section.travel_time_of_edge = 0
        start_route_section.minimum_fare = 0

        start_route_section.parent_info = Location(
            start_route_section.parent_node, start_route_section.stop_type).location_info
        start_route_section.child_info = Location(
            start_route_section.child_node, start_route_section.stop_type).location_info

        walking_time_to_src_id_after_walk = 0
        time_from_src_id_to_dst_id = route_sections_list[-1].travel_time_of_edge
        walking_time_to_dst_id_after_walk = 0

        if src_id_after_walk != src_id:
            walking_edge_at_start, walking_time_to_src_id_after_walk = self.walking_mode.get_walk_edge_static_bus(
                src_id, src_id_after_walk, time, section_id=0, is_last_section=False)
            route_sections_list.insert(0, walking_edge_at_start)
            # route_sections_list[-1].travel_time_of_edge = walking_time_to_src_id_after_walk

        last_route_section = route_sections_list[-1]
        last_route_section.arrival_time = self.convAdd(
            time, walking_time_to_src_id_after_walk + time_from_src_id_to_dst_id
        )
        last_route_section.departure_time = last_route_section.arrival_time

        if dst_id != dst_id_before_walk:
            walk_edge_at_end, walking_time_to_dst_id_after_walk = self.walking_mode.get_walk_edge_static_bus(
                dst_id_before_walk, dst_id, time, section_id=None, is_last_section=True)
            route_sections_list.append(walk_edge_at_end)

        last_route_section = route_sections_list[-1]
        last_route_section.arrival_time = self.convAdd(
            time, walking_time_to_src_id_after_walk + time_from_src_id_to_dst_id + walking_time_to_dst_id_after_walk
        )
        last_route_section.departure_time = last_route_section.arrival_time

        route_sections_list.insert(0, start_route_section)

        return [route_sections_list]  # this is list of route.

    @staticmethod
    def get_route_data_in_format(src_id: int, dst_id: int, rtx, routes_data_list) -> list:
        """
        Function to get the route data in the required format.
        The required format is a list of :
            [[route_id_list], src_id_after_walk, dst_id_before_walk]
        args:
            src_id: int
            dst_id: int
            rtx: str (route type can be rt1, rt2, rt3, rt4)
            routes_data_list: str (A string representation of list of routes)
            routes_data_list for rt1 can be like: [route_id_list]
            routes_data_list for rt2 can be a list of like: [[route_id_list], src_id_after_walk]
            routes_data_list for rt3 can be a list of like: [[route_id_list], dst_id_before_walk]
            routes_data_list for rt4 can be a list of like: [[route_id_list], src_id_after_walk, dst_id_before_walk]
        return:
            List[List] (A list of route data in the required format)
        """
        try:
            routes_data_list: list = json.loads(routes_data_list)
        except TypeError:
            routes_data_list: list = routes_data_list
        except json.JSONDecodeError:
            routes_data_list: list = routes_data_list
        except Exception as e:
            logger.debug(f"Error in getting route data in format: {e}")
            logger.info(f"Error in getting route data in format could not get the routes.")
            return []

        if not list(routes_data_list):
            return []

        if rtx[-3:] == 'rt1':
            route_id_list: list = routes_data_list
            formatted_routes_data_list: list = [[route_id_list, src_id, dst_id]]
        else:
            formatted_routes_data_list: list = []
            for route_data in routes_data_list:
                if rtx[-3:] == 'rt2':
                    route_id_list = route_data[0]
                    src_id_after_walk = route_data[1]
                    formatted_routes_data_list.append([route_id_list, src_id_after_walk, dst_id])
                elif rtx[-3:] == 'rt3':
                    route_id_list = route_data[0]
                    dst_id_before_walk = route_data[1]
                    formatted_routes_data_list.append([route_id_list, src_id, dst_id_before_walk])
                else:
                    formatted_routes_data_list.append(route_data)

        return formatted_routes_data_list

    def get_static_zero_hop_routes(self, src: NearestStop, dst: NearestStop, time: str, unique_route_ids: list):
        """
        Function to get the static zero hop routes.
        args:
            src: NearestStop
            dst: NearestStop
            time: str
            unique_route_ids: list
        return:
            List[List[BusRouteSection]], List
        """
        src_id: int = src.stop_id
        dst_id: int = dst.stop_id
        logger.debug(f"Getting the static zero hop routes for {src_id} and {dst_id}.")

        # zero_hop_query: str = f'select rt1, rt2, rt3, rt4 from zero_hop where src is {src_id} and dest is {dst_id};'
        zero_hop_query: str = f'select rt1 from zero_hop where src is {src_id} and dest is {dst_id};'
        zero_hop_result = self.fetch_result(self.zero_hop_conn, zero_hop_query)

        static_zero_hop_routes: list = []

        if not zero_hop_result:
            logger.debug(f"Could not get the zero hop results from zero hop database for {src_id} and {dst_id}.")
            return static_zero_hop_routes, []

        for row in zero_hop_result:
            row_data = dict(row)
            for rtx, routes_data_list in row_data.items():
                routes_data_list: list = self.get_route_data_in_format(src_id, dst_id, rtx, routes_data_list)
                # routes_data_list = [
                #                       [[route_id_list], src_id_after_walk, dst_id_before_walk],
                #                       [[route_id_list], src_id_after_walk, dst_id_before_walk],
                #                       [[route_id_list], src_id_after_walk, dst_id_before_walk],
                #                           .......            ......             .........
                #                    ]
                if not routes_data_list:
                    continue

                for route_data in routes_data_list:
                    # route_data: [[route_id_list], src_id_after_walk, dst_id_before_walk
                    route: List[BusRouteSection] = self.get_route(src, dst, route_data, time)
                    static_zero_hop_routes.append(route)

        combined_static_zero_hop_routes = itertools.chain.from_iterable(static_zero_hop_routes)
        final_static_zero_hop_routes = []

        for route in combined_static_zero_hop_routes:
            route = self.add_schedule(route, MAXIMUM_LEGS_ALLOWED_NON_MULTI)
            if route:
                final_static_zero_hop_routes.append(route)

        if len(list(combined_static_zero_hop_routes)) != 0 and len(final_static_zero_hop_routes) == 0:
            logger.debug(
                f"Could not get the static zero hop routes for {src_id} and {dst_id}, routes dropped in add schedule.")

        final_static_zero_hop_routes = sorted(
            [route for route in final_static_zero_hop_routes if route],
            key=lambda rt: self.get_waiting_time(rt[0].arrival_time, rt[-1].arrival_time)
        )

        unique_static_zero_hop_routes = []
        static_count = 0
        for route in final_static_zero_hop_routes:
            temp_route_ids = route[1].route_id

            if temp_route_ids == [-1]:
                temp_route_ids = route[2].route_id

            comm = sum([1 for _id in temp_route_ids if _id in unique_route_ids])
            if comm == 0:
                for route_section in route:
                    if route_section.vehicle_id:
                        route_section.vehicle_id = ''

                unique_static_zero_hop_routes.append(route)
                unique_route_ids.extend(temp_route_ids)
                static_count += 1
            else:
                continue

            if static_count == PER_TYPE_PATHS:
                break

        return unique_static_zero_hop_routes, unique_route_ids

    # alter of direction_new.
    def get_routes(self, src: NearestStop,
                   dst: NearestStop,
                   time_from_stop: str,
                   time_from_location: str,
                   modify_route: bool = True) -> tuple:  # TODO: The entire direction runs here. Modify to only include zero-hop-route + real-time. Perhaps this structure of the function will change for all.
        """
        Main function responsible to get the routes from source to destination for bus.
        args:
            src: NearestStop
            dst: NearestStop
            time_from_stop: str
            time_from_location: str
            modify_route: bool
        return:
            List[List[BusRouteSection]], List[List[BusRouteSection]], List[List[BusRouteSection]]
        """
        src_id: int = src.stop_id
        dst_id: int = dst.stop_id

        unique_static_zero_hop_routes: list = []
        unique_static_one_hop_routes: list = []

        unique_route_ids: list = []

        if not self.compare_elements(src_id, dst_id):
            return unique_static_zero_hop_routes, unique_static_one_hop_routes

        # TODO: Get the results here, start, mid (for one hop) and end. Pass those to respective functions to complete the responses using the databases.
        if self.allow_zero_hop:
            (
                unique_static_zero_hop_routes,
                unique_route_ids
            ) = self.get_static_zero_hop_routes(src, dst, time_from_stop,
                                                unique_route_ids)  # TODO: This runs from v to v_ and completes the result in the traditional format

        if self.allow_one_hop and len(unique_static_zero_hop_routes) < 3:
            (
                unique_static_one_hop_routes,
                unique_route_ids
            ) = self.get_static_one_hop_routes(src, dst, time_from_stop,
                                               unique_route_ids)  # TODO: This runs from v to v___ and completes the result in the traditional format. As the results are already found, this function is to be modified to just fill the response

        unique_static_zero_hop_routes = self.evaluate_parent_child_node_info(unique_static_zero_hop_routes)
        unique_static_one_hop_routes = self.evaluate_parent_child_node_info(unique_static_one_hop_routes)

        if not modify_route:
            return unique_static_zero_hop_routes, unique_static_one_hop_routes

        unique_static_zero_hop_routes = [
            self.modify_route(src, dst, route, time_from_location, BusRouteSection)
            for route in unique_static_zero_hop_routes
        ]

        unique_static_one_hop_routes = [
            self.modify_route(src, dst, route, time_from_location, BusRouteSection)
            for route in unique_static_one_hop_routes
        ]

        return unique_static_zero_hop_routes, unique_static_one_hop_routes

    def get_static_one_hop_routes(self, src, dst, time, unique_route_ids):
        logger.debug("Getting the static one hop routes.")
        try:
            src_id = int(self.cluster_details[src.stop_id])
            dst_id = int(self.cluster_details[dst.stop_id])
        except KeyError as e:
            logger.info("Could not find the reverse mapping in the cluster for one hop results.")
            logger.debug(f"Could not find the reverse mapping in the cluster for one hop results.")
            return [], unique_route_ids

        try:
            candidate_paths = list(nx.all_shortest_paths(BUS_GRAPH, source=str(src_id), target=str(dst_id) + '_' * 3))
            candidate_paths_stripped = [[int(x.strip('_')) for x in row] for row in candidate_paths]
        except nx.exception.NetworkXNoPath as e:
            logger.info('Could not find one hop results for source {} and destination {}.'.format(src_id, dst_id))
            logger.debug('Could not find one hop results for source {} and destination {}.'.format(src_id, dst_id))
            return [], unique_route_ids
        zero_hop_query: str = "select rt1 from zero_hop where src is {} and dest is {};"
        notional_routes = []
        for cp in candidate_paths_stripped:
            if len(cp) == 3:
                c_routes1 = [
                    eval(dict(self.fetch_result(self.zero_hop_conn, zero_hop_query.format(cp[0], cp[1]))[0])['rt1']),
                    cp[0], cp[1]]
                c_routes2 = [
                    eval(dict(self.fetch_result(self.zero_hop_conn, zero_hop_query.format(cp[1], cp[2]))[0])['rt1']),
                    cp[1], cp[2]]
                notional_routes.append([*cp, c_routes1, c_routes2])
            else:
                c_routes1 = [
                    eval(dict(self.fetch_result(self.zero_hop_conn, zero_hop_query.format(cp[0], cp[1]))[0])['rt1']),
                    cp[0], cp[1]]
                c_routes2 = [
                    eval(dict(self.fetch_result(self.zero_hop_conn, zero_hop_query.format(cp[2], cp[3]))[0])['rt1']),
                    cp[2], cp[3]]
                notional_routes.append([cp[0], cp[1], cp[3], c_routes1, c_routes2])
        routes: List[List[
            BusRouteSection]] = self.get_routes_one_hop(notional_routes, time)

        final_routes = []
        for route in routes:
            copied_route = [copy.copy(route_section) for route_section in route]
            path = self.add_schedule(copied_route, MAXIMUM_LEGS_ALLOWED_NON_MULTI)
            if path:
                final_routes.append(path)

        static_one_hop_routes = sorted(
            [x for x in final_routes if x],
            key=lambda x: self.get_waiting_time(x[0].arrival_time, x[-1].arrival_time)
        )

        unique_static_one_hop_routes = []
        static_count = 0

        for route in static_one_hop_routes:
            temp_route = list(itertools.chain.from_iterable(
                [x for x in set(tuple(x) for x in [x.route_id for x in route[1:] if x.route_id != [-1]])]))

            comm = sum([1 for x in temp_route if x in unique_route_ids])
            if comm != 0:
                continue
            else:
                for route_section in route:
                    if route_section.vehicle_id != '':
                        route_section.vehicle_id = ''

                unique_static_one_hop_routes.append(route)
                unique_route_ids.extend(temp_route)
                static_count += 1

                if static_count == PER_TYPE_PATHS:
                    break

        return unique_static_one_hop_routes, unique_route_ids

    def get_routes_one_hop(self, notional_routes: List[tuple], time):
        # notional_routes: [ (src, mid, dst, x, y), (src, mid, dst, x, y), (src, mid, dst, x, y) ]
        # x, y are of [[route_id_list], src_id_after_walk, dst_id_before_walk] type

        routes_list: List[List[BusRouteSection]] = []
        for src_id, mid, dst_id, srt_x, drt_y in notional_routes:

            if srt_x[0] == drt_y[0] or set(srt_x[0]).intersection(set(drt_y[0])):
                continue

            leg1_routes_list = self.get_route(src_id, mid, srt_x, time)
            if not leg1_routes_list:
                continue

            leg2_routes_list = self.get_route(mid, dst_id, drt_y, time)
            if not leg2_routes_list:
                continue

            routes: List[List[BusRouteSection]] = []
            for leg1_route in leg1_routes_list:
                for leg2_route in leg2_routes_list:
                    leg1_route_copy = [copy.copy(route_section) for route_section in leg1_route]
                    leg2_route_copy = [copy.copy(route_section) for route_section in leg2_route]

                    leg2_route_copy[1].arrival_time = leg1_route_copy[-1].arrival_time
                    leg2_route_copy[1].vehicle_id = 1

                    dst_before_walk_in_second_leg = drt_y[2]
                    if dst_before_walk_in_second_leg != dst_id:
                        leg2_route_copy[-2].arrival_time = self.convAdd(
                            leg2_route_copy[1].arrival_time,
                            leg2_route_copy[-2].travel_time_of_edge
                        )

                    leg2_route_copy[-1].arrival_time = self.convAdd(
                        leg2_route_copy[1].arrival_time,
                        leg2_route_copy[-1].travel_time_of_edge
                    )

                    route: List[BusRouteSection] = leg1_route_copy + leg2_route_copy[1:]
                    routes.append(route)
            routes_list.extend(routes)

        return routes_list
