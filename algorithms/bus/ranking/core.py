import copy
from datetime import datetime
from algorithms.common.ranking.core import BaseRanking
from modules.logger import logger
from modules.miscellaneous import get_peak_off_peak_category
from algorithms.bus.config import UPDATED_FREQ_OCT_PATH
from modules.miscellaneous import access_with_handle
import pickle


class BusRanking(BaseRanking):
    def __init__(self):
        super().__init__()
        self.frequency = self.load_frequency()

    @staticmethod
    def load_frequency():
        # with open(UPDATED_FREQ_OCT_PATH, 'rb') as freq:
        frequency_file_handler = access_with_handle(UPDATED_FREQ_OCT_PATH, open, FileNotFoundError, place_holder=None, args=True, must=False, mode='rb')
        if frequency_file_handler:
            frequency = pickle.load(frequency_file_handler)
            frequency_file_handler.close()
            return frequency
        else:
            logger.warning("Can not load frequency to use in BusRanking algorithms.")
            return {}

    def remove_duplicate(self, possible_options, grouped=False):
        if not self.remove_duplicate_result:
            return possible_options

        _possible_options = [copy.copy(i) for i in possible_options]
        existing_routes = []

        for idx, route in enumerate(possible_options):
            routes_in_this = []

            for route_section in route:
                route_section_route_id = route_section.route_id
                if route_section_route_id is not None and list(route_section_route_id) not in routes_in_this:
                    routes_in_this.append(list(route_section_route_id))

            for route_id in routes_in_this:
                if grouped:
                    if route_id != [-1]:
                        if route_id in existing_routes:
                            _possible_options.remove(route)
                        else:
                            existing_routes.append(route_id)
                        break
                else:
                    if route_id != [-1]:
                        if route_id in existing_routes:
                            _possible_options.remove(route)
                        else:
                            existing_routes.append(route_id)
                        break

        return _possible_options

    def rank_result(self, time, static_responses_zero=None, static_responses_one=None,
                    grouped=False):

        possible_options_static = self._get_possible_options(
            time, static_responses_zero, static_responses_one
        )

        possible_options = []
        if static_responses_zero is not None and static_responses_one is not None:
            options = self.remove_duplicate(possible_options_static, grouped)
            possible_options.extend(options)


        elif static_responses_zero is not None:
            options = self.remove_duplicate(possible_options_static, grouped)
            possible_options.extend(options)

        elif static_responses_one is not None:
            options = self.remove_duplicate(possible_options_static, grouped)
            possible_options.extend(options)
        else:
            possible_options = []

        possible_options = self.filter_responses(possible_options)
        return possible_options

    def get_current_frequency(self, route_id, query_time=None):
        if query_time is None:
            query_time = datetime.now().hour
        else:
            query_time = int(query_time.split(':')[0])

        category = get_peak_off_peak_category(query_time)
        try:
            return self.frequency[int(route_id)][category]
        except KeyError:
            logger.info(f"Can not find frequency for route_id: {route_id}, category: {category}, route_id might not present.")
            return -1
        except Exception:
            logger.info(f"Can not find frequency for route_id: {route_id}, category: {category}, category fro this route_id might not present.")
            return -1

    def get_ranked_results(self, route_ids):
        ranked = {}
        for r in route_ids:
            ranked[r] = self.get_current_frequency(r)
        print(ranked)
        v = dict(sorted(ranked.items(), key=lambda x: x[1]))
        resp = [x for x in (list(v.keys())) if v[x] != -1][:3]
        return resp if len(resp) > 0 else list(v.keys())[:3]  # return top 3 if no frequency is available
