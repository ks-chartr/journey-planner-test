from algorithms.multimodal.core import MultiModal
from algorithms.multimodal.algorithm.v2 import MultiModalAlgorithmsV2
from algorithms.multimodal.ranking.v2 import MultiModalRankingV2


class MultiModalV2(MultiModal):

    def __init__(self):
        super().__init__()
        self.algorithms = MultiModalAlgorithmsV2()
        self.ranking = MultiModalRankingV2()
