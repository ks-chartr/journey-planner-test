from algorithms.bus.core import Bus
from algorithms.bus.algorithm.v2 import BusAlgorithmsV2
from algorithms.bus.ranking.v2 import BusRankingV2


class BusV2(Bus):

    def __init__(self):
        super().__init__()
        self.algorithms_v2 = BusAlgorithmsV2()
        self.ranking_v2 = BusRankingV2()
