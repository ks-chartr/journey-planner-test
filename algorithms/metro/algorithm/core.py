"""
This module contains the core algorithms for Metro.
"""

from modules.logger import logger
import json
from algorithms.common.algorithm.core import BaseAlgorithms
from algorithms.metro.config import METRO_SCHEDULE_DB_PATH, METRO_RESPONSE_DB_PATH
from modules.constants import *
from models.models import MetroRouteSection
from algorithms.metro.config import METRO_FARE_LIST
from models.models import Location


class MetroAlgorithms(BaseAlgorithms):
    """
    Class to implement the core algorithms for Metro.
    """

    def __init__(self):
        """
        Constructor for MetroAlgorithms.
        """
        super().__init__()
        self.schedule_connection = self.connectDB(METRO_SCHEDULE_DB_PATH)
        self.response_connection = self.connectDB(METRO_RESPONSE_DB_PATH)
        self.response_table_name = 'metro_response'
        self.route_section = MetroRouteSection
        self.mode = METRO_ENUM
        self.MAX_DAY_TIME = '23:59:59'
        self.metro_fare = METRO_FARE_LIST
        self.leg_transfer_time = METRO_LEG_TRANSFER_TIME
        self.index_offset = METRO_STOP_INDEX_OFFSET

    def get_dept_time(self, route_section, dept_time, init=True):
        stop_id = route_section.parent_node
        route_id = route_section.route_id

        if init is False:
            dept_time = self.convAdd(dept_time, 420)

        if not self.compare_elements(route_id, [-1]):
            return dept_time

        query = f"""select min(departure_time) from metro_schedule 
                    where stop_id is {stop_id} and route_id is {route_id[0]} 
                    and departure_time > '{dept_time}';"""

        departure_time = self.fetch_result(self.schedule_connection, query)[0][0]

        if departure_time is None or self.get_waiting_time(dept_time, departure_time) > WAITING_TIME_THRESHOLD:
            return None

        return departure_time

    def evaluate_parent_child_node_info(self, routes):
        for route in routes:
            for route_section in route:
                route_section.child_info = Location(route_section.child_node, self.mode).location_info
                route_section.parent_info = Location(route_section.parent_node, self.mode).location_info
        return routes

    def get_route(self, route_response, time):
        route = []
        leg_count = 0
        for route_section_id, route_section_list in enumerate(route_response):
            route_section = self.route_section()
            route_section.section_id = route_section_id
            route_section.child_node = route_section_list[0]
            route_section.parent_node = route_section_list[1]
            route_section.route_id = [route_section_list[2]]
            route_section.travel_time_of_edge = route_section_list[6]

            route_section.child_info = Location(route_section.child_node, route_section.stop_type).location_info
            route_section.parent_info = Location(route_section.parent_node, route_section.stop_type).location_info

            if route_section_id == 0:
                route_section.arrival_time = route_section.departure_time = time

            if route_section_id == 1:
                route_section.departure_time = time

            if route_section.travel_time_of_edge:
                leg_count += 1
                if leg_count > 1:
                    route_section.travel_time_of_edge -= 4 * 120

                route_section.departure_time = self.convAdd(time, route_section.travel_time_of_edge)

                if route_section_id == len(route_response):
                    route_section.arrival_time = route_section.departure_time
                else:
                    route_section.arrival_time = self.convAdd(route_section.departure_time, self.leg_transfer_time)

            route.append(route_section)

        return route

    def get_metro_route(self, src_ids, dst_ids, time_to_src_dict):

        src_ids, dst_ids = self.get_src_ids_and_dst_ids(src_ids, dst_ids, self.index_offset)
        time_to_src_dict = {
            (key - self.index_offset if key > self.index_offset else key): value
            for key, value in time_to_src_dict.items()
        }

        query = f'select response from {self.response_table_name} where source in {src_ids} and destination in {dst_ids}'

        try:
            responses = self.fetch_result(self.response_connection, query)
        except Exception as e:
            logger.error(f"Error in fetching response from metro_response: {e}")
            responses = []

        routes_list = []

        for src_dst_response in responses:
            src_dst_response = json.loads(src_dst_response[0])
            if not src_dst_response:
                continue

            src_dst_response = [src_dst_response[0]]

            for route_response in src_dst_response:
                try:
                    time_from_stop = time_to_src_dict[route_response[0][0]]
                except KeyError:
                    raise KeyError(
                        f"Time at stop {route_response[0][1]} not found in Metro route."
                    )

                route = self.get_route(route_response, time_from_stop)
                if not route:
                    continue

                start_route_section = route[0]
                end_route_section = route[-1]

                try:
                    end_route_section.fare = self.metro_fare[
                        start_route_section.child_node
                    ][
                        end_route_section.child_node
                    ]
                except (KeyError, IndexError) as e:
                    logger.debug(
                        f"""
                        Error {e} in getting fare from {start_route_section.child_node} to 
                        {end_route_section.child_node}
                        """
                    )
                    logger.info(
                        f"""
                        Fare not found from {start_route_section.child_node} to {end_route_section.child_node}")
                        """)
                    end_route_section.fare = 10

                routes_list.append(route)

        return routes_list

    
    def get_routes(self, src, dst, time_from_stop, time_from_location, modify_route=True):

        src_ids = [src.stop_id]
        dst_ids = [dst.stop_id]

        routes_list = []

        time_at_src_dict = {src.stop_id: time_from_stop}
        metro_routes_list = self.get_metro_route(src_ids, dst_ids, time_at_src_dict)

        for route in metro_routes_list:
            route = self.add_schedule(route, MAXIMUM_LEGS_ALLOWED_NON_MULTI)
            if not route:
                continue

            route = self.evaluate_parent_child_node_info([route])[0]
            if modify_route:
                modified_route = self.modify_route(src, dst, route, time_from_location, self.route_section)
            else:
                modified_route = route
            routes_list.append(modified_route)

        return routes_list
