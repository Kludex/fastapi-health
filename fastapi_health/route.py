from typing import Callable, List


class HealthRoute:
    def __init__(self, conditions: List[Callable]):
        self.conditions = conditions

    def __call__(self) -> bool:
        return all([condition() for condition in self.conditions])
