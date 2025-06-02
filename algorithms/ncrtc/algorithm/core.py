"""
This module contains the core algorithms for NCRTC.
"""

from modules.logger import logger
import json
from algorithms.metro.algorithm.core import MetroAlgorithms
from algorithms.ncrtc.config import NCRTC_SCHEDULE_DB_PATH, NCRTC_RESPONSE_DB_PATH
from modules.constants import *
from models.models import NCRTCRouteSection
from models.models import Location
from django.core.cache import cache


class NCRTCAlgorithms(MetroAlgorithms):
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

    def get_ncrtc_route(self, src_ids, dst_ids, time_to_src_dict):
        cache_key = f'ncrtc_route_{src_ids}_{dst_ids}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        routes = super().get_metro_route(src_ids, dst_ids, time_to_src_dict)
        cache.set(cache_key, routes, TIMESTAMP_CACHE_TIMEOUT)

        return routes
