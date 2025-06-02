from algorithms.common.algorithm.core import BaseAlgorithms
from modules.distance_apis import get_walk_info
from models.models import WalkRouteSection, Location
from algorithms.common.core import BaseParent
from algorithms.walk.algorithm.core import WalkingAlgorithm
from models.models import Route
from modules.constants import WALK_ENUM
from modules.logger import logger

class Walk(BaseParent):
    def __init__(self) -> None:
        super().__init__()
        self.walk__algorithm = WalkingAlgorithm()

    def get_src_dst_for_walk(self, src, src_name, src_cords, dst, dst_name, dst_cords):
        pass


    def get_response_type(self, response):
        pass

    def get_route_fare(self, route):
        pass

    def get_response(self, request_data):
        pass

    def get_color(self, route):
        pass

    def get_route(self, route_section, mode_to_reach_transit):
        route = Route()

        route.route = WALK_ENUM
        route.routes = [WALK_ENUM]
        route.type = WALK_ENUM
        route.short_name = ''
        route.long_name = f" towards "
        route.agency = ''
        route.vehicle_id = ''
        route.occupancy = ''
        route.departure_time = route_section.departure_time
        route.ending_time = ''
        route.color = '#4D4D4D'
        route.description = ''
        route.trip_time = ''
        route.fare = 0
        route.available_options = []
        route.stops = []
        route.polyline = ''
        route.frequency = -1

        return route

    @staticmethod
    def drop_results_with_excess_walk(response, src, dst):
        updated_response = []

        try:
            direct_walk_time = round(get_walk_info(src.location_value, dst.location_value)[1] / 60)
        except Exception as e:
            direct_walk_time = 10000

        for res in response:
            total_walk_time = 0
            total_time = res['trip_time']
            for rt in res['directions']['routes']:
                if rt['route'] == 'walk':
                    total_walk_time += rt['trip_time']

            if total_walk_time <= direct_walk_time:
                updated_response.append(res)
            else:
                print(f'Dropped result, total_walk_time: {total_walk_time}, direct_walk_time: {direct_walk_time}')
            print(f'total_time : {total_time}')
            print(f'total_walk_time : {total_walk_time}')
            print(f'direct_walk_time : {direct_walk_time}')

        return updated_response
