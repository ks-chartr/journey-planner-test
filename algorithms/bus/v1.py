from algorithms.bus.core import Bus
from algorithms.bus.algorithm.v1 import BusAlgorithmsV1
from algorithms.bus.ranking.v1 import BusRankingV1


class BusV1(Bus):

    def __init__(self):
        super().__init__()
        self.algorithms= BusAlgorithmsV1()
        self.ranking = BusRankingV1()
