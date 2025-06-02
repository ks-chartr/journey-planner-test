from algorithms.multimodal.core import MultiModal
from algorithms.multimodal.algorithm.v1 import MultiModalAlgorithmsV1
from algorithms.multimodal.ranking.v1 import MultiModalRankingV1


class MultiModalV1(MultiModal):

    def __init__(self):
        super().__init__()
        self.algorithms = MultiModalAlgorithmsV1()
        self.ranking = MultiModalRankingV1()
