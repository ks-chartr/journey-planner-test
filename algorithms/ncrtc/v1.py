from algorithms.ncrtc.core import NCRTC
from algorithms.ncrtc.algorithm.v1 import NCRTCAlgorithmsV1
from algorithms.ncrtc.ranking.v1 import NCRTCRankingV1


class NCRTCV1(NCRTC):

    def __init__(self):
        super().__init__()
        self.algorithms = NCRTCAlgorithmsV1()
        self.ranking = NCRTCRankingV1()
