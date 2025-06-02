from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import copy
from modules.constants import MAXIMUM_TRAVEL_TIME_OF_ROUTE, MAXIMUM_PATHS_PER_HOP_TYPE


class BaseRanking(ABC):

    def __init__(self):
        self.remove_duplicate_result = True
        self.maximum_travel_time_of_leg = MAXIMUM_TRAVEL_TIME_OF_ROUTE

    def turn_off_duplicate(self):
        self.remove_duplicate_result = True

    def turn_on_duplicate(self):
        self.remove_duplicate_result = False

    @staticmethod
    def distance_filter(possible_options):
        route_id_route_group_map = {}

        for route_group in possible_options:
            route_id = []
            total_x_distance = 0
            for route_edge in route_group:
                zero_th_route_id = route_edge[1].route_id
                edge_distance = route_edge[1].birds_distance
                if zero_th_route_id not in [-1, [-1]]:
                    route_id.extend(zero_th_route_id)
                else:
                    total_x_distance += edge_distance

            if tuple(route_id) not in route_id_route_group_map:
                route_id_route_group_map[tuple(route_id)] = []
            route_id_route_group_map[tuple(route_id)].append((total_x_distance, route_group))

        route_id_route_group_map = {
            route_id: sorted(dist_route_grp_pair, key=lambda dist_route: dist_route[0])[:MAXIMUM_PATHS_PER_HOP_TYPE]
            for route_id, dist_route_grp_pair in route_id_route_group_map.items()
        }

        final_possible_options = []

        for route_id_set, dist_route_grp_pair in route_id_route_group_map.items():
            for dist, route_grp in dist_route_grp_pair:
                final_possible_options.append(route_grp)

        return final_possible_options

    @staticmethod
    @abstractmethod
    def remove_duplicate(possible_options, grouped=False):
        pass

    def filter_responses(self, ranked_responses):

        if not ranked_responses:
            return ranked_responses

        filtered_responses = []
        fastest_route_time = self.subtract_times(ranked_responses[0][-1].arrival_time,
                                                 ranked_responses[0][0].arrival_time)

        for ranked_routes in ranked_responses:
            filtered_routes = []
            idx = 0

            if self.subtract_times(
                    ranked_routes[-1].arrival_time, ranked_routes[0].arrival_time
            ) > fastest_route_time * 2:
                continue

            for i in range(1, len(ranked_routes)):
                if ranked_routes[i].route_id == ranked_routes[i - 1].route_id:
                    filtered_routes[idx].append(ranked_routes[i])
                else:
                    if i == 1:
                        filtered_routes.append([ranked_routes[0]])
                    else:
                        filtered_routes.append([ranked_routes[i - 1]])
                        idx += 1
                    filtered_routes[idx].append(ranked_routes[i])

            filtered_responses.append(filtered_routes)
        return filtered_responses

    @abstractmethod
    def rank_result(self, time, static_responses_zero=None, static_responses_one=None,
                    grouped=False):
        pass

    @staticmethod
    def get_stops_dict(stops_df):
        stops_df.rename(columns={'stop_id': 'id', 'stop_name': 'name', 'stop_lat': 'lat', 'stop_lon': 'lon'},
                        inplace=True)
        stops_df['idx'] = stops_df.loc[:, 'id']
        stops_dict = stops_df[['idx', 'id', 'name', 'lat', 'lon']].set_index('idx').T.to_dict()
        del stops_df

        return stops_dict

    @staticmethod
    def subtract_times(t1, t2):
        datetime1 = datetime.strptime(t1, "%H:%M:%S")
        datetime2 = datetime.strptime(t2, "%H:%M:%S")

        time_diff = datetime1 - datetime2

        if time_diff < timedelta(0):
            time_diff += timedelta(86400)

        time_diff_seconds = time_diff.total_seconds()

        return time_diff_seconds

    @staticmethod
    def get_datetime_given_time(time):
        _datetime = datetime.strptime(time, '%H:%M:%S')
        return _datetime

    def sort_on_total_time(self, possible_options, response_type):

        filtered_total_times = {
                idx: x[-1].travel_time_of_edge for idx, x in enumerate(possible_options)
                if x[-1].travel_time_of_edge <= self.maximum_travel_time_of_leg
            }

        order = [k[0] for k in sorted(filtered_total_times.items(), key=lambda x: x[1])]
        return [possible_options[k] for k in order]

    def sort_on_total_time_updated(self, possible_options):

        sr = {}
        for idx, opt in enumerate(possible_options):
            sr[idx] = self.subtract_times(opt[-1].arrival_time, opt[0].arrival_time)

        sr = sorted(sr.items(), key=lambda item: item[1])
        order = [k[0] for k in sr if 0 < k[1] < self.maximum_travel_time_of_leg]  # Drop above 5 hours

        return [possible_options[k] for k in order]

    def sort_on_total_time_from_now(self, possible_options, query_time):
        _possible_options = copy.deepcopy(possible_options)
        options_dict = {}
        all_reach_by_list = []

        for idx, route in enumerate(possible_options):
            reach_by = self.get_datetime_given_time(route[-1].arrival_time)
            current_time = self.get_datetime_given_time(query_time)
            all_reach_by_list.append(route[-1].arrival_time)
            options_dict[route[-1].arrival_time] = route
            st = reach_by - current_time

            if st.total_seconds() >= self.maximum_travel_time_of_leg:  # drop results which are 3 hours away
                if idx != 0:
                    _possible_options.remove(route)
                    all_reach_by_list.remove(route[-1].arrival_time)

        all_reach_by_list = sorted(all_reach_by_list)
        _possible_options_ = []
        for i in all_reach_by_list:
            _possible_options_.append(options_dict[i])

        return _possible_options_

    def _get_possible_options(
            self, time, static_responses_zero=None, static_responses_one=None
    ):
        possible_options_static = None


        if static_responses_zero is not None:
            possible_options_static = self.sort_on_total_time_updated(static_responses_zero)
        if static_responses_one is not None:
            if possible_options_static is None:
                possible_options_static = self.sort_on_total_time_updated(static_responses_one)
            else:
                possible_options_static += self.sort_on_total_time_updated(static_responses_one)

        self.sort_on_total_time_from_now(possible_options_static, time)

        return possible_options_static
