from algorithms.multimodal.ranking.core import MultiModalRanking
from modules.constants import MAXIMUM_TRAVEL_TIME_OF_NCRTC_ROUTE


class MultiNCRTCRanking(MultiModalRanking):
    def __init__(self):
        super().__init__()
        self.maximum_travel_time_of_leg = MAXIMUM_TRAVEL_TIME_OF_NCRTC_ROUTE

