from algorithms.ncrtc.core import NCRTC
from algorithms.ncrtc.algorithm.v2 import NCRTCAlgorithmsV2
from algorithms.ncrtc.ranking.v2 import NCRTCRankingV2


class NCRTCV2(NCRTC):

    def __init__(self):
        super().__init__()
        self.algorithms = NCRTCAlgorithmsV2()
        self.ranking = NCRTCRankingV2()
