import copy

from algorithms.common.algorithm.core import BaseAlgorithms
from algorithms.metro.algorithm.core import MetroAlgorithms
from algorithms.bus.algorithm.core import BusAlgorithms
from modules.constants import *
from modules.constants import METRO_TYPE_ENUM
from models.models import Location, MultiRouteSection, RouteSection
import pandas as pd
from models.models import NearestStop
from typing import List
import json


class MultiModalAlgorithms(BaseAlgorithms):

    def __init__(self):
        super().__init__()
        self.mode = "multi"
        self.stops = None
        self.metro_algorithm = MetroAlgorithms()
        self.bus_algorithm = BusAlgorithms()
        self.allow_multi_hop = True

    def turn_off_multi_hop(self):
        self.allow_multi_hop = False
        self.bus_algorithm.turn_off_one_hop()

    def get_dept_time(self, route_section, dept_time, init=True):
        edge_type = route_section.edge_type

        if edge_type == BUS_TYPE_ENUM:
            dept_time = self.bus_algorithm.get_dept_time(route_section, dept_time, init)
        elif edge_type == METRO_TYPE_ENUM:
            dept_time = self.metro_algorithm.get_dept_time(route_section, dept_time, init)
        return dept_time

    def evaluate_parent_child_node_info(self, routes: List[List[MultiRouteSection]]):
        for route in routes:
            for route_section in route:
                route_section.child_info = Location(
                    route_section.child_node, route_section.child_node_stop_type
                ).location_info

                route_section.parent_info = Location(
                    route_section.parent_node, route_section.parent_node_stop_type
                ).location_info
        return routes

    def trunc_results(self, inp_list):
        visited = []
        inp_list = iter(
            sorted(
                [x for x in inp_list if x != []],
                key=lambda x: self.get_waiting_time(x[0].arrival_time, x[-1].arrival_time))
        )
        new_r = []
        count = 0
        for res in inp_list:
            rts = set([tuple(x.route_id) for x in res[1:] if x.route_id not in [-1, [-1]]])
            if rts in visited:
                continue

            visited.append(rts)
            new_r.append(res)
            count += 1

            if count == MULTI_ROUTE_COUNT:
                break
        return new_r

    def only_bus_route(self, src, dst, time_at_src, time_at_location):
        src_id = src.stop_id
        dst_id = dst.stop_id

        src_type = src.stop_type
        dst_type = dst.stop_type

        src_name = src.stop_name
        dst_name = dst.stop_name

        src_tkt_code = src.tkt_code
        dst_tkt_code = dst.tkt_code

        stops_from_src: List[NearestStop] = self.get_nearest_stops_from_location(src_id, src_type, BUS_TYPE_ENUM,
                                                                                 src_name, src_tkt_code)
        stops_from_dst: List[NearestStop] = self.get_nearest_stops_from_location(dst_id, dst_type, BUS_TYPE_ENUM,
                                                                                 dst_name, dst_tkt_code)

        only_bus_routes = []

        for src_new in stops_from_src:
            walk_duration_from_src_to_src_new_after_walk = src_new.travel_time
            time_at_src_new = self.convAdd(time_at_src, walk_duration_from_src_to_src_new_after_walk)

            multi_edge_at_start = MultiRouteSection()
            multi_edge_at_start.child_node = src_id
            multi_edge_at_start.child_node_stop_type = src_type
            multi_edge_at_start.parent_node = src_id
            multi_edge_at_start.parent_node_stop_type = src_type
            multi_edge_at_start.edge_type = src_type
            multi_edge_at_start.departure_time = time_at_src
            multi_edge_at_start.arrival_time = time_at_src
            multi_edge_at_start.travel_time = 0
            multi_edge_at_start.distance = 0
            multi_edge_at_start.birds_distance = 0
            multi_edge_at_start.route_id = None

            # w_e = [[src, src, None, time, time, 0, 0, 0, '', ''],
            #        [s, src, [-1], begin_time, time, '', first_walk_time, '', 'walk', metro_dict[src][s]]]

            starting_edges = [multi_edge_at_start]

            if src_new.stop_id != src_id:
                walking_edge = MultiRouteSection()
                walking_edge.child_node = src_new.stop_id
                walking_edge.child_node_stop_type = src_new.stop_type
                walking_edge.parent_node = src.stop_id
                walking_edge.parent_node_stop_type = src.stop_type
                walking_edge.edge_type = WALK_TYPE_ENUM
                walking_edge.route_id = [-1]
                walking_edge.departure_time = time_at_src
                walking_edge.arrival_time = time_at_src_new
                walking_edge.travel_time_of_edge = walk_duration_from_src_to_src_new_after_walk
                walking_edge.distance = src_new.distance
                walking_edge.birds_distance = src_new.birds_distance
                starting_edges.append(walking_edge)

            for dst_new in stops_from_dst:
                if src_new.stop_id == dst_new.stop_id and src_new == dst_new:
                    continue

                all_route_groups = self.bus_algorithm.get_routes(
                    src_new, dst_new, time_at_src_new, time_at_location, modify_route=False
                )

                for route_group in all_route_groups:
                    for route in route_group:
                        route = [MultiRouteSection().transform(route_section, BUS_TYPE_ENUM) for route_section in route]

                        start_walk_exist, end_walk_exist = False, False
                        first_route_section: RouteSection = route[1]
                        last_route_section: RouteSection = route[-1]

                        if first_route_section.route_id in [-1, [-1]]:
                            first_route_section.parent_node = src_id
                            first_route_section.departure_time = time_at_src
                            first_route_section.travel_time_of_edge += src_new.travel_time
                            first_route_section.distance = src_new.distance
                            first_route_section.birds_distance = src_new.birds_distance
                            start_walk_exist = True

                        if last_route_section.route_id in [-1, [-1]]:
                            last_route_section.parent_node = dst_id
                            last_route_section.arrival_time = self.convAdd(
                                last_route_section.arrival_time, dst_new.travel_time
                            )
                            last_route_section.travel_time_of_edge += dst_new.travel_time
                            last_route_section.distance = dst_new.distance
                            last_route_section.birds_distance = dst_new.birds_distance
                            end_walk_exist = True

                        last_walk_edge = MultiRouteSection()
                        last_walk_edge.child_node = dst_id
                        last_walk_edge.child_node_stop_type = dst_type
                        last_walk_edge.parent_node = last_route_section.child_node
                        last_walk_edge.parent_node_stop_type = BUS_TYPE_ENUM
                        last_walk_edge.route_id = [-1]
                        last_walk_edge.arrival_time = self.convAdd(
                            last_route_section.arrival_time, dst_new.travel_time
                        )
                        last_walk_edge.departure_time = last_route_section.arrival_time
                        last_walk_edge.travel_time_of_edge = dst_new.travel_time
                        last_walk_edge.distance = dst_new.distance
                        last_walk_edge.birds_distance = dst_new.birds_distance
                        last_walk_edge.edge_type = WALK_TYPE_ENUM

                        if start_walk_exist:
                            if end_walk_exist:
                                new_route = [starting_edges[0]] + route[1:]
                            else:
                                new_route = [starting_edges[0]] + route[1:] + [last_walk_edge]
                        else:
                            if end_walk_exist:
                                new_route = starting_edges + route[1:]
                            else:
                                new_route = starting_edges + route[1:] + [last_walk_edge]

                        only_bus_routes.append(new_route)

        return only_bus_routes

    def get_bus_transfer_points(self, src_ids, dst_ids):
        src_ids, dst_ids = self.get_src_ids_and_dst_ids(src_ids, dst_ids, BUS_STOP_INDEX_OFFSET)
        query = f'''select src, dest, rt1 from zero_hop where src in {src_ids} and dest in {dst_ids}'''
        return pd.read_sql(query, con=self.bus_algorithm.zero_hop_conn)

    def get_initial_walk_edge(self, src, src_new, time_at_src):

        first_route_section = MultiRouteSection()
        first_route_section.child_node = src.stop_id
        first_route_section.child_node_stop_type = src.stop_type
        first_route_section.parent_node = src.stop_id
        first_route_section.parent_node_stop_type = src.stop_type
        first_route_section.route_id = None
        first_route_section.departure_time = time_at_src
        first_route_section.arrival_time = time_at_src
        first_route_section.edge_type = src.stop_type
        first_route_section.travel_time_of_edge = 0

        second_route_section = MultiRouteSection()
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

        return [first_route_section, second_route_section]

    def get_src_dst_information(self, src, dst, required_src_type, required_dst_type, src_offset, dst_offset):
        src_id = src.stop_id
        dst_id = dst.stop_id

        src_type = src.stop_type
        dst_type = dst.stop_type

        src_name = src.stop_name
        dst_name = dst.stop_name

        src_tkt_code = src.tkt_code
        dst_tkt_code = dst.tkt_code

        if src_type == required_src_type:
            src_to_start = [NearestStop(stop_id=src_id - src_offset, stop_name=src_name, stop_code=src_tkt_code,
                                        stop_type=src_type, geometry='', distance=0, birds_distance=0,
                                        travel_time=0, source_name="")]
        else:
            src_to_start = self.get_nearest_stops_from_location(src_id, src_type, required_src_type, src_name, src_tkt_code)

        if dst_type == required_dst_type:
            dst_to_reach = [NearestStop(stop_id=dst_id - dst_offset, stop_name=dst_name, stop_code=dst_tkt_code,
                                        stop_type=dst_type,geometry='', distance=0, birds_distance=0, travel_time=0,
                                        source_name="")]
        else:
            dst_to_reach = self.get_nearest_stops_from_location(dst_id, dst_type, required_dst_type, dst_name, dst_tkt_code)

        if not (src_to_start and dst_to_reach):
            return [], [], [], []

        src_id_dict = {src.stop_id: src for src in src_to_start}
        src_id_list = list(src_id_dict.keys())

        dst_for_transfer_dict = self.get_nearest_stops_from_location(
            None, required_src_type, required_dst_type, None, dst_tkt_code
        )

        return src_id_dict, src_id_list, dst_to_reach, dst_for_transfer_dict

    def bus_metro_routes(self, src, dst, time_at_src, time_at_location):
        # Mode1: BUS_TYPE_ENUM
        # Mode2: METRO_TYPE_ENUM
        # Mode1-----Transfer Point-----Mode2
        #                 ||
        # (Bus stops) ------ (bus stops---walk---metro stops) ------ (metro stops)

        (
            src_id_dict, src_id_list, dst_to_reach, dst_for_transfer_dict
        ) = self.get_src_dst_information(
            src, dst, BUS_TYPE_ENUM, METRO_TYPE_ENUM, BUS_STOP_INDEX_OFFSET, METRO_STOP_INDEX_OFFSET
        )

        if not (src_id_dict and src_id_list and dst_to_reach):
            return []

        bus_transfer_points_df = self.get_bus_transfer_points(src_id_list, tuple(dst_for_transfer_dict.keys()))
        if not len(bus_transfer_points_df):
            return []

        bus_transfer_points_df["metro_tp"] = bus_transfer_points_df["dest"].map(dst_for_transfer_dict)

        routes = []
        for row in bus_transfer_points_df.itertuples():
            bus_src, bus_dest, metro_src_data, available_routes = row.src, row.dest, row.metro_tp, row.rt1
            travel_time_to_bus_src_from_src = src_id_dict[bus_src].travel_time
            time_at_bus_src = self.convAdd(time_at_src, travel_time_to_bus_src_from_src)

            routes_data_list = self.bus_algorithm.get_route_data_in_format(bus_src, bus_dest, 'rt1', available_routes)
            if not routes_data_list:
                continue

            bus_routes = []
            for route_data in routes_data_list:
                raw_bus_route = self.bus_algorithm.get_route(bus_src, bus_dest, route_data, time_at_bus_src)
                if not raw_bus_route:
                    continue
                else:
                    bus_routes.extend(raw_bus_route)

            if not bus_routes:
                continue

            metro_src_ids = tuple([src_id for src_id in metro_src_data])
            metro_dst_ids = tuple([dst.stop_id for dst in dst_to_reach])

            time_at_src_dict = {}
            for i, bus_route in enumerate(bus_routes):
                arrival_time_at_transfer_point = bus_route[-1].arrival_time
                for metro_src_id, walk_distance_in_transfer in metro_src_data.items():
                    walk_time_in_transfer = int(walk_distance_in_transfer * 3600 / 3.5)
                    if metro_src_id not in time_at_src_dict:
                        time_at_src_dict[metro_src_id] = self.convAdd(arrival_time_at_transfer_point, walk_time_in_transfer)

            metro_routes = self.metro_algorithm.get_metro_route(metro_src_ids, metro_dst_ids, time_at_src_dict)
            if not metro_routes:
                continue

            for i, bus_route in enumerate(bus_routes):
                bus_routes[i] = [
                    MultiRouteSection().transform(route_section, BUS_TYPE_ENUM) for route_section in bus_route
                ]
                bus_route: List[MultiRouteSection] = bus_routes[i]

                for j, metro_route in enumerate(metro_routes):
                    metro_routes[j] = [
                        MultiRouteSection().transform(route_section, METRO_TYPE_ENUM) for route_section in metro_route
                    ]

                multi_routes = []
                initial_walk_edge = self.get_initial_walk_edge(src, src_id_dict[bus_src], time_at_src)

                for metro_route in metro_routes:
                    walk_route = MultiRouteSection()
                    walk_route.child_node = metro_route[0].child_node
                    walk_route.parent_node = bus_route[-1].child_node
                    walk_route.route_id = [-1]

                    walk_distance_of_transfer = metro_src_data[metro_route[0].child_node]
                    walk_time_of_transfer = int(walk_distance_of_transfer * 3600 / 3.5)
                    walk_route.travel_time_of_edge = walk_time_of_transfer
                    walk_route.arrival_time = self.convAdd(bus_route[-1].arrival_time, walk_route.travel_time_of_edge)
                    walk_route.child_node_stop_type = METRO_TYPE_ENUM
                    walk_route.parent_node_stop_type = BUS_TYPE_ENUM
                    walk_route.edge_type = WALK_TYPE_ENUM
                    walk_route.distance = walk_distance_of_transfer
                    walk_route.birds_distance = walk_distance_of_transfer

                    if src.stop_type == BUS_TYPE_ENUM:
                        multi_route = bus_route + [walk_route] + metro_route[1:]
                    else:
                        multi_route = initial_walk_edge + bus_route[1:] + [walk_route] + metro_route[1:]
                    multi_routes.append(multi_route)
                routes.extend(multi_routes)

        routes = self.add_last_walk_edge(dst, METRO_TYPE_ENUM, dst_to_reach, routes)
        return routes

    def add_last_walk_edge(self, dst, dst_type_to_reach, dst_to_reach, routes):
        if dst.stop_type == dst_type_to_reach:
            return routes
        else:
            final_routes = []
            dst_stop_id_dict = {dst.stop_id: dst for dst in dst_to_reach}
            for route in routes:
                walk_route = MultiRouteSection()
                walk_route.child_node = dst.stop_id
                walk_route.parent_node = route[-1].child_node
                walk_route.route_id = [-1]
                walk_distance_of_transfer = dst_stop_id_dict[walk_route.parent_node].distance
                walk_time_of_transfer = int(walk_distance_of_transfer * 3600 / 3.5)
                walk_route.travel_time_of_edge = walk_time_of_transfer
                walk_route.arrival_time = self.convAdd(route[-1].arrival_time, walk_route.travel_time_of_edge)
                walk_route.child_node_stop_type = dst.stop_type
                walk_route.parent_node_stop_type = dst_type_to_reach
                walk_route.edge_type = WALK_TYPE_ENUM
                walk_route.distance = walk_distance_of_transfer
                walk_route.birds_distance = walk_distance_of_transfer
                final_routes.append(route + [walk_route])
            return final_routes

    def get_metro_transfer_points(self, src_ids, dst_ids):
        src_ids, dst_ids = self.get_src_ids_and_dst_ids(src_ids, dst_ids, METRO_STOP_INDEX_OFFSET)
        query = f'''select source, destination from metro_response where source in {src_ids} and destination in
                     {dst_ids} and response <> \'[]\' '''
        src_to_dst_list = self.fetch_result(self.metro_algorithm.response_connection, query)

        src_list = [src for (src, _) in src_to_dst_list]
        dst_list = [dst for (_, dst) in src_to_dst_list]

        return src_list, dst_list

    def get_bus_routes(self, src_list, dst_list, time_dict):
        src_ids = [src.stop_id for src in src_list]
        dst_ids = [dst.stop_id for dst in dst_list]

        src_ids, dst_ids = self.get_src_ids_and_dst_ids(src_ids, dst_ids, BUS_STOP_INDEX_OFFSET)
        query = f"""
            select src, dest, rt1 
            from zero_hop 
            where src in {src_ids} and dest in {dst_ids} and src <> dest and rt1 <> '[]'
        """
        available_routes_data = self.fetch_result(self.bus_algorithm.zero_hop_conn, query)

        bus_routes_reference_dict = {}
        for (src_id, dst_id, raw_route_data) in available_routes_data:
            raw_route_data = json.loads(raw_route_data)
            if not raw_route_data:
                continue

            routes_data_list = self.bus_algorithm.get_route_data_in_format(src_id, dst_id, 'rt1', raw_route_data)
            if not routes_data_list:
                continue

            for metro_route_id, time_at_bus_src_dict in time_dict.items():
                if (src_id, dst_id) not in time_at_bus_src_dict:
                    continue
                time_at_bus_src = time_at_bus_src_dict[(src_id, dst_id)]

                for route_data in routes_data_list:
                    raw_bus_routes = self.bus_algorithm.get_route(src_id, dst_id, route_data, time_at_bus_src)

                    raw_bus_routes = [
                        [MultiRouteSection().transform(route_section, BUS_TYPE_ENUM) for route_section in raw_bus_route]
                        for raw_bus_route in raw_bus_routes
                    ]

                    if not raw_bus_routes:
                        continue
                    else:
                        if metro_route_id not in bus_routes_reference_dict:
                            bus_routes_reference_dict[metro_route_id] = []
                        bus_routes_reference_dict[metro_route_id].extend(raw_bus_routes)

        return bus_routes_reference_dict

    def metro_bus_routes(self, src, dst, time_at_src, time_at_location):
        # Mode1: METRO_TYPE_ENUM
        # Mode2: BUS_TYPE_ENUM
        # Mode1-----Transfer Point-----Mode2
        #                 ||
        # (Metro stops) ------ (metro stops---walk---bus stops) ------ (bus stops)

        (
            src_id_dict, src_id_list, dst_to_reach, dst_for_transfer_dict
        ) = self.get_src_dst_information(
            src, dst, METRO_TYPE_ENUM, BUS_TYPE_ENUM, METRO_STOP_INDEX_OFFSET, BUS_STOP_INDEX_OFFSET
        )

        if not (src_id_dict and src_id_list and dst_to_reach):
            return []

        metro_src_ids, metro_dst_ids = self.get_metro_transfer_points(src_id_list, tuple(dst_for_transfer_dict.keys()))
        time_at_metro_src_dict = {
            src_id: self.convAdd(time_at_src, src_id_dict[src_id].travel_time) for src_id in metro_src_ids
        }
        metro_routes = self.metro_algorithm.get_metro_route(metro_src_ids, metro_dst_ids, time_at_metro_src_dict)
        for metro_route in metro_routes:
            self.metro_algorithm.add_schedule(metro_route, MAXIMUM_LEGS_ALLOWED_NON_MULTI)

        if not metro_routes:
            return []

        metro_routes_reference_dict = {}
        metro_route_id = 0
        time_at_bus_src_reference_dict = {}
        bus_stops_at_transfer_point = []

        for metro_route in metro_routes:
            metro_route = [
                MultiRouteSection().transform(route_section, METRO_TYPE_ENUM) for route_section in metro_route
            ]
            metro_route_src_id = metro_route[0].parent_node
            initial_edges = self.get_initial_walk_edge(src, src_id_dict[metro_route_src_id], time_at_src)

            if src.stop_type != METRO_TYPE_ENUM:
                metro_route = initial_edges + metro_route[1:]

            metro_route_dst_id = metro_route[-1].child_node
            bus_stops_at_this_transfer_point = self.get_nearest_stops_from_location(
                metro_route_dst_id, METRO_TYPE_ENUM, BUS_TYPE_ENUM, None, None
            )

            metro_routes_reference_dict[metro_route_id] = metro_route
            time_at_bus_src_reference_dict[metro_route_id] = {
                (src.stop_id, dst.stop_id): self.convAdd(metro_route[-1].arrival_time, src.travel_time)
                for src in bus_stops_at_this_transfer_point for dst in dst_to_reach
            }
            bus_stops_at_transfer_point.extend(bus_stops_at_this_transfer_point)
            metro_route_id += 1

        bus_routes_reference_dict = self.get_bus_routes(bus_stops_at_transfer_point, dst_to_reach,
                                                        time_at_bus_src_reference_dict)
        bus_stops_at_transfer_point_dict = {bus_stop.stop_id: bus_stop for bus_stop in bus_stops_at_transfer_point}

        routes = []
        for metro_route_id, metro_route in metro_routes_reference_dict.items():
            if metro_route_id not in bus_routes_reference_dict:
                continue

            bus_routes = bus_routes_reference_dict[metro_route_id]
            for bus_route in bus_routes:
                walking_edge = MultiRouteSection()
                walking_edge.child_node = bus_route[0].child_node
                walking_edge.child_node_stop_type = BUS_TYPE_ENUM
                walking_edge.parent_node = metro_route[-1].child_node
                walking_edge.parent_node_stop_type = METRO_TYPE_ENUM
                walking_edge.route_id = [-1]
                walking_edge.edge_type = WALK_TYPE_ENUM
                walking_edge.departure_time = metro_route[-1].arrival_time
                walking_edge.arrival_time = self.convAdd(
                    walking_edge.departure_time, bus_stops_at_transfer_point_dict[walking_edge.child_node].travel_time)
                walking_edge.distance = bus_stops_at_transfer_point_dict[walking_edge.child_node].distance
                walking_edge.birds_distance = bus_stops_at_transfer_point_dict[walking_edge.child_node].birds_distance
                walking_edge.travel_time_of_edge = bus_stops_at_transfer_point_dict[walking_edge.child_node].travel_time

                routes.append(metro_route + [walking_edge] + bus_route[1:])

        routes = self.add_last_walk_edge(dst, BUS_TYPE_ENUM, dst_to_reach, routes)
        return routes

    def get_routes(self, src, dst, time_from_stop, time_from_location, modify_route=True):

        only_bus_routes = self.only_bus_route(src, dst, time_from_stop, time_from_location)
        only_bus_routes = self.trunc_results(only_bus_routes)

        all_routes = only_bus_routes
        if self.allow_multi_hop:
            bus_metro_routes = self.bus_metro_routes(src, dst, time_from_stop, time_from_location)
            bus_metro_routes = [self.add_schedule(route, MAXIMUM_LEGS_ALLOWED_MULTI) for route in bus_metro_routes]
            bus_metro_routes = [route for route in bus_metro_routes if route]
            bus_metro_routes = self.trunc_results(bus_metro_routes)

            metro_bus_routes = self.metro_bus_routes(src, dst, time_from_stop, time_from_location)
            metro_bus_routes = [self.add_schedule(route, MAXIMUM_LEGS_ALLOWED_MULTI) for route in metro_bus_routes]
            metro_bus_routes = [route for route in metro_bus_routes if route]
            metro_bus_routes = self.trunc_results(metro_bus_routes)

            all_routes += bus_metro_routes + metro_bus_routes

        all_routes = self.evaluate_parent_child_node_info(all_routes)

        if not modify_route:
            return all_routes

        modified_routes = []
        for route in all_routes:
            if not route:
                continue

            new_route = [copy.copy(rt) for rt in route]
            new_route = self.modify_route(src, dst, new_route, time_from_location, MultiRouteSection)
            new_route[0].route_id = None
            modified_routes.append(new_route)

        return modified_routes
