from algorithms.metro.ranking.core import MetroRanking
from modules.constants import MAXIMUM_TRAVEL_TIME_OF_NCRTC_ROUTE


class NCRTCRanking(MetroRanking):
    def __init__(self):
        super().__init__()
        self.maximum_travel_time_of_leg = MAXIMUM_TRAVEL_TIME_OF_NCRTC_ROUTE

