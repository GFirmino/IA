from dataclasses import dataclass, field
from typing import List


@dataclass(order=True)
class FrontierNode:
    priority: float
    city: str = field(compare=False)
    path: List[str] = field(compare=False, default_factory=list)
    cost: float = field(compare=False, default=0.0)
    depth: int = field(compare=False, default=0)
