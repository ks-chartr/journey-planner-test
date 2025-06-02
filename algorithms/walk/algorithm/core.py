from algorithms.common.algorithm.core import BaseAlgorithms
from algorithms.bus.config import WALK_DISTANCE_DETAILS
from models.models import WalkRouteSection, Location
from modules.constants import *

class WalkingAlgorithm(BaseAlgorithms):

    def __init__(self):
        super().__init__()
        self.mode = 'walk'

    def evaluate_parent_child_node_info(self, routes):
        pass

    def get_dept_time(self, route_section, departure_time, init=True, edge_type=None):
        pass

    def get_routes(self, src, dst, time_from_stop, time_from_location, modify_route=True):
        pass

    def get_walk_edge_static_bus(self, src_id, dst_id, time, section_id=0, is_last_section=False, mode=BUS_ENUM):
        walk_distance_from_src_dst = WALK_DISTANCE_DETAILS[dst_id][src_id]
        walk_time_from_src_dst = int(walk_distance_from_src_dst * 3600 / 3.5)
        arrival_time = self.convAdd(time, walk_time_from_src_dst)

        walking_route_section = WalkRouteSection()
        walking_route_section.section_id = section_id
        walking_route_section.child_node = dst_id
        walking_route_section.child_node_stop_type = mode
        walking_route_section.parent_node = src_id
        walking_route_section.parent_node_stop_type = mode
        walking_route_section.route_id = [-1]
        walking_route_section.arrival_time = arrival_time
        walking_route_section.departure_time = arrival_time
        walking_route_section.is_last_section = is_last_section
        walking_route_section.travel_time_of_edge = walk_time_from_src_dst
        walking_route_section.distance = walk_distance_from_src_dst
        walking_route_section.birds_distance = walk_distance_from_src_dst
        walking_route_section.child_info = Location(dst_id, mode).location_info
        walking_route_section.parent_info = Location(src_id, mode).location_info

        return walking_route_section, walk_time_from_src_dst
