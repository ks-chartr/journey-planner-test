import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from algorithms.bus.config import METRO_TO_BUS_DICT, BUS_TO_METRO_DICT
from models.models import Location, WalkRouteSection, ParkRideRouteSection
from models.models import NearestStop
from modules.constants import *
from modules.logger import logger


class BaseAlgorithms(ABC):

    def __init__(self):
        self.MAX_DAY_TIME = '23:59:59'
        self.mode = None
        self.metro_to_bus_dict = self.modify_mode_dict(METRO_TO_BUS_DICT, METRO_STOP_INDEX_OFFSET,
                                                       BUS_STOP_INDEX_OFFSET)
        self.bus_to_metro_dict = self.modify_mode_dict(BUS_TO_METRO_DICT, BUS_STOP_INDEX_OFFSET,
                                                       METRO_STOP_INDEX_OFFSET)
        self.index_offsets = {
            METRO_ENUM: METRO_STOP_INDEX_OFFSET,
            BUS_ENUM: BUS_STOP_INDEX_OFFSET,
            NCRTC_ENUM: NCRTC_STOP_INDEX_OFFSET,
        }

    @abstractmethod
    def get_dept_time(self, route_section, dept_time, init=True):
        pass

    @abstractmethod
    def evaluate_parent_child_node_info(self, routes):
        pass

    @staticmethod
    def modify_mode_dict(mode_dict, mode_1_offset, mode_2_offset):
        new_mode_dict = {}
        for key, value in mode_dict.items():
            new_mode_dict[key - mode_1_offset] = {
                k - mode_2_offset: v for k, v in value.items()
            }
        return new_mode_dict

    @staticmethod
    def allot_section_ids(route):
        for i, route_section in enumerate(route):
            route_section.section_id = i

    @staticmethod
    def get_src_ids_and_dst_ids(src_ids: list, dst_ids: list, offset: int):
        src_ids: list = [
            src_id - offset if src_id >= offset else src_id for src_id in src_ids
        ]
        dst_ids: list = [
            dst_id - offset if dst_id >= offset else dst_id for dst_id in dst_ids
        ]

        src_ids: tuple = tuple(src_ids) if len(src_ids) != 1 else f'({src_ids[0]})'
        dst_ids: tuple = tuple(dst_ids) if len(dst_ids) != 1 else f'({dst_ids[0]})'

        return src_ids, dst_ids

    def get_stops_from_type_a_to_type_b(self, type_a, type_b, stop_id_a=None):
        if type_a == type_b:
            return [(stop_id_a, 0)]
        else:
            if type_a == METRO_TYPE_ENUM:
                if type_b == BUS_TYPE_ENUM:
                    if stop_id_a is None:
                        return self.metro_to_bus_dict
                    else:
                        return [
                            (stop_id_b, int(self.metro_to_bus_dict[stop_id_a][stop_id_b] * 3600 / 3.5))
                            for stop_id_b in list(self.metro_to_bus_dict[stop_id_a].keys())
                        ] if stop_id_a in self.metro_to_bus_dict else []
                return []

            elif type_a == BUS_TYPE_ENUM:
                if type_b == METRO_TYPE_ENUM:
                    if stop_id_a is None:
                        return self.bus_to_metro_dict
                    else:
                        return [
                            (stop_id_b, int(self.bus_to_metro_dict[stop_id_a][stop_id_b] * 3600 / 3.5))
                            for stop_id_b in list(self.bus_to_metro_dict[stop_id_a].keys())
                        ] if stop_id_a in self.bus_to_metro_dict else []
                return []
            return []

    def get_nearest_stops_from_location(
            self, location_id, from_location_type, to_location_type, location_name, location_code,
            location_distance=0, location_time=0
    ):
        locations = self.get_stops_from_type_a_to_type_b(
            type_a=from_location_type, type_b=to_location_type, stop_id_a=location_id
        )

        if location_id is None:
            return locations

        nearest_stops = []

        for stop_id, walk_time in locations:
            distance = walk_time * (3.5 / 3600) + location_distance
            walk_time += location_time
            nearest_stop = NearestStop(
                stop_id=stop_id, stop_type=to_location_type, stop_name=location_name, stop_code=location_code,
                geometry='', distance=distance, birds_distance=distance, travel_time=walk_time, source_name="")
            nearest_stops.append(nearest_stop)

        return nearest_stops

    def modify_initial_leg(self, route):
        zeroth_route_section = route[0]
        first_route_section = route[1]
        last_route_section = route[-1]

        arrival_time = zeroth_route_section.arrival_time
        if len(route) < MAXIMUM_LEGS_FOR_PENALIZATION:
            arrival_time = self.convAdd(arrival_time, INITIAL_TIME_PENALTY_FOR_ROOT)

        departure_time = self.get_dept_time(first_route_section, arrival_time)

        if departure_time is None:
            return []

        else:
            zeroth_route_section.departure_time = first_route_section.departure_time = departure_time

            if departure_time > self.MAX_DAY_TIME:
                return []
            else:
                last_route_section.arrival_time = self.convAdd(departure_time, last_route_section.travel_time_of_edge)
                if len(route) > 2:
                    last_route_section.departure_time = ''

        return route

    def modify_middle_leg(self, route_section, dept_time):
        zeroth_route_section = route_section[0]
        last_route_section = route_section[-1]
        dept_time = self.convAdd(dept_time, TRANSFER_ROUTE_PENALTY)

        departure_time = self.get_dept_time(zeroth_route_section, dept_time, False)

        if departure_time is None or departure_time > self.MAX_DAY_TIME:
            logger.debug(
                f"Departure time not found for route_section {zeroth_route_section.child_node} - {last_route_section.child_node}")
            return []

        if departure_time == dept_time:
            last_route_section.departure_time = departure_time
            last_route_section.arrival_time = self.convAdd(departure_time, last_route_section.travel_time_of_edge)
        else:
            zeroth_route_section.departure_time = departure_time
            last_route_section.arrival_time = self.convAdd(departure_time, last_route_section.travel_time_of_edge)

            if len(route_section) > 1:
                last_route_section.departure_time = zeroth_route_section.arrival_time = ''

        return route_section

    def add_schedule(self, route, allowed_legs):
        self.allot_section_ids(route)
        leg_start_section_ids = self.get_legs(route)

        if len(leg_start_section_ids) > allowed_legs:
            logger.info(f"""Skipping the route because of exceeding maximum legs allowed, allowed legs: 
            {allowed_legs} < {len(leg_start_section_ids)}""")
            return None

        if len(leg_start_section_ids) == 1:
            route = self.modify_initial_leg(route)
            return route

        first_leg_section_start_id = leg_start_section_ids[0]
        first_leg_section_end_id = leg_start_section_ids[1]

        first_leg_section = route[first_leg_section_start_id: first_leg_section_end_id]
        first_leg_section = self.modify_initial_leg(first_leg_section)

        if not first_leg_section:
            return first_leg_section

        for i in range(1, len(leg_start_section_ids) - 1):
            ith_leg_section_start_id = leg_start_section_ids[i]
            ith_leg_section_end_id = leg_start_section_ids[i + 1]

            just_previous_leg_end_route_section_id = leg_start_section_ids[i] - 1
            just_previous_leg_end_route_section = route[just_previous_leg_end_route_section_id]

            ith_leg_section = route[ith_leg_section_start_id: ith_leg_section_end_id]
            ith_leg_section = self.modify_middle_leg(ith_leg_section,
                                                     just_previous_leg_end_route_section.arrival_time)

            if not ith_leg_section:
                return ith_leg_section

        last_leg_section_start_id = leg_start_section_ids[-1]
        last_leg_section = route[last_leg_section_start_id:]

        second_last_leg_end_route_section_id = last_leg_section_start_id - 1
        second_last_leg_end_route_section = route[second_last_leg_end_route_section_id]

        last_leg_section = self.modify_middle_leg(last_leg_section, second_last_leg_end_route_section.arrival_time)
        if not last_leg_section:
            return last_leg_section

        last_leg_section_last_route_section = last_leg_section[-1]

        if len(last_leg_section) > 1:
            last_leg_section_last_route_section.departure_time = last_leg_section_last_route_section.arrival_time

        if last_leg_section_last_route_section.route_id == [-1]:
            last_leg_section_last_route_section.departure_time = second_last_leg_end_route_section.arrival_time

        return route

    @abstractmethod
    def get_routes(self, src, dst, time_from_stop, time_from_location, modify_route=True):
        pass

    @staticmethod
    def get_waiting_time(time1, time2):
        time1, time2 = str(time1).split(':'), str(time2).split(':')
        hours_2_sec2, min_2_sec2, hours_2_sec1, min_2_sec1 = (int(time2[0]) % 24) * 60 * 60, int(time2[1]) * 60, (
                int(time1[0]) % 24) * 60 * 60, int(time1[1]) * 60
        tot_sec1 = hours_2_sec1 + min_2_sec1 + int(float(time1[2]))
        tot_sec2 = hours_2_sec2 + min_2_sec2 + int(float(time2[2]))
        if tot_sec2 - tot_sec1 < 0:
            return tot_sec2 - tot_sec1 + (24 * 3600)
        return tot_sec2 - tot_sec1

    @staticmethod
    def compare_elements(a: object, b: object) -> bool:
        if isinstance(a, int) and isinstance(b, int):
            return a != b
        elif (isinstance(a, list) and isinstance(b, list)) or (isinstance(a, tuple) and isinstance(b, tuple)):
            return sorted(a) != sorted(b)
        else:
            return True

    @staticmethod
    def connectDB(db_path: str, mode: str = 'ro', return_dict: bool = False):
        try:
            if mode == 'ro':
                conn: sqlite3.Connection = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True, check_same_thread=False)
            else:
                conn: sqlite3.Connection = sqlite3.connect(f'file:{db_path}?mode=rw', uri=True, check_same_thread=False)

            if return_dict:
                conn.row_factory = sqlite3.Row

            return conn

        except sqlite3.OperationalError as e:
            logger.error(f"Can not open connection for db path: {db_path}")
            return None

    @staticmethod
    def fetch_result(conn, query: str):
        c = conn.cursor()
        result = c.execute(query).fetchall()
        c.close()
        return result

    @staticmethod
    def func4(TSTR):
        val = TSTR.split('.')
        val = val[0].split(':')
        h, m, s = int(val[0]), int(val[1]), int(val[2])
        dt = datetime(1900, 1, 1, h, m, s)
        return dt

    def convAdd(self, dept_time, timediff):
        x = self.func4(dept_time)
        x += timedelta(seconds=int(timediff))
        return str(x.time())

    def get_legs(self, route):
        leg_start_section_ids = [0]

        for route_section_id in range(1, len(route) - 1):
            current_route_section = route[route_section_id]
            next_route_section = route[route_section_id + 1]

            if self.compare_elements(current_route_section.route_id, next_route_section.route_id):
                leg_start_section_ids.append(next_route_section.section_id)
            else:
                current_route_section.arrival_time = ''

        return leg_start_section_ids

    def modify_route(self, src, dst, route, time, TransitRouteSection):

        if src.distance > 0.01:
            if route[1].route_id in [-1, [-1]]:  # First leg walk
                route[0].child_node = route[0].parent_node = route[1].parent_node = -1
                route[0].arrival_time = route[0].departure_time = time

                route[1].travel_time_of_edge += int(src.travel_time)
                route[1].departure_time = time
                route[1].distance += src.distance
                route[1].birds_distance += src.birds_distance
                route[1].geometry = src.geometry
                transit_route = TransitRouteSection()
                transit_route.child_node = transit_route.parent_node = -1
                transit_route.route_id = None
                transit_route.arrival_time = transit_route.departure_time = time

            else:

                route[0].route_id = [-1]
                route[0].parent_node = -1
                route[0].departure_time = time
                route[0].travel_time_of_edge = int(src.travel_time)
                route[0].distance = src.distance
                route[0].birds_distance = src.birds_distance
                route[0].geometry = src.geometry

                if route[0].route_id in [-50, [-50]]:
                    changed_route = ParkRideRouteSection()
                    changed_route.psa = src.data['psa']
                    changed_route.meta_info = src.data['meta_info']
                    changed_route.map_dict = src.data['map_dict']

                    changed_route.section_id = route[0].section_id
                    changed_route.route_id = route[0].route_id
                    changed_route.parent_node = route[0].parent_node
                    changed_route.child_node = route[0].child_node
                    changed_route.departure_time = route[0].departure_time
                    changed_route.arrival_time = route[0].arrival_time
                    changed_route.travel_time_of_edge = route[0].travel_time_of_edge
                    changed_route.distance = route[0].distance
                    changed_route.birds_distance = route[0].birds_distance
                    changed_route.is_last_section = route[0].is_last_section
                    changed_route.geometry = route[0].geometry
                    changed_route.stop_type = route[0].stop_type
                    changed_route.edge_type = route[0].edge_type
                    changed_route.parent_info = route[0].parent_info
                    changed_route.child_info = route[0].child_info
                    changed_route.vehicle_id = route[0].vehicle_id
                    route[0] = changed_route

                transit_route = TransitRouteSection()
                transit_route.child_node = transit_route.parent_node = -1
                transit_route.route_id = None
                transit_route.arrival_time = transit_route.departure_time = time
                route = [transit_route] + route

        if dst.distance > 0.01:
            if route[-1].route_id in [-1, [-1]]:
                route[-1].child_node = -2
                route[-1].arrival_time = self.convAdd(route[-1].arrival_time, int(dst.travel_time))
                route[-1].travel_time_of_edge += int(dst.travel_time)
                route[-1].distance += dst.distance
                route[-1].birds_distance += dst.birds_distance
                route[-1].geometry = dst.geometry
            else:
                last_section = route[-1]
                last_stop_id = last_section.child_node
                arrival_time_at_last_stop = last_section.arrival_time

                transit_route = WalkRouteSection()
                transit_route.child_node = -2
                transit_route.parent_node = last_stop_id
                transit_route.route_id = [-1]
                transit_route.arrival_time = self.convAdd(arrival_time_at_last_stop, int(dst.travel_time))
                transit_route.departure_time = arrival_time_at_last_stop
                transit_route.travel_time_of_edge = int(dst.travel_time)
                transit_route.distance = dst.distance
                transit_route.edge_type = WALK_TYPE_ENUM
                transit_route.birds_distance = dst.birds_distance
                transit_route.parent_info = Location(last_stop_id, dst.stop_type).location_info
                transit_route.geometry = dst.geometry
                route.append(transit_route)
        return route
