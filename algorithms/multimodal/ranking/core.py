import copy
from datetime import datetime
from algorithms.common.ranking.core import BaseRanking
from algorithms.bus.ranking.core import BusRanking


class MultiModalRanking(BaseRanking):

    def remove_duplicate(self, possible_options, grouped=False):
        if not self.remove_duplicate_result:
            return possible_options

        _possible_options = []
        routes_in_this = []

        for idx, route in enumerate(possible_options):
            rts = []
            for route_section in route:
                if route_section.route_id == -1:
                    rts.append(route_section.route_id)
                elif route_section.route_id not in rts:
                    rts.append(route_section.route_id)

            if rts is not None and rts not in routes_in_this:
                routes_in_this.append(rts)
                _possible_options.append(route)

        return _possible_options

    def rank_result(
            self, time, static_responses_zero=None, static_responses_one=None, grouped=False
    ):
        possible_options_static = self._get_possible_options(
            time, static_responses_zero, static_responses_one
        )
        possible_options = self.remove_duplicate(possible_options_static)
        possible_options = self.filter_responses(possible_options)
        possible_options = self.distance_filter(possible_options)

        return possible_options
