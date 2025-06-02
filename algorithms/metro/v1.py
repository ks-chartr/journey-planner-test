from algorithms.metro.core import Metro
from algorithms.metro.algorithm.v1 import MetroAlgorithmsV1
from algorithms.metro.ranking.v1 import MetroRankingV1


class MetroV1(Metro):

    def __init__(self):
        super().__init__()
        self.algorithms = MetroAlgorithmsV1()
        self.ranking = MetroRankingV1()
