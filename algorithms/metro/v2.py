from algorithms.metro.core import Metro
from algorithms.metro.algorithm.v2 import MetroAlgorithmsV2
from algorithms.metro.ranking.v2 import MetroRankingV2


class MetroV2(Metro):

    def __init__(self):
        super().__init__()
        self.algorithms = MetroAlgorithmsV2()
        self.ranking = MetroRankingV2()
