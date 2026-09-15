from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ItemSpec:
    cost: int
    score: int


ITEMS: dict[str, ItemSpec] = {
    "apple": ItemSpec(cost=3, score=6),
    "carrot": ItemSpec(cost=2, score=4),
    "berry": ItemSpec(cost=4, score=8),
    "snack_pack": ItemSpec(cost=10, score=20),
    "drink": ItemSpec(cost=6, score=13),
    "ball": ItemSpec(cost=5, score=0),
}

DELAYED_ITEMS = frozenset({"apple", "drink"})
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")


def get_rank(score: int) -> str:
    if score >= 200:
        return "ENPC Architect"
    if score >= 100:
        return "ENPC Booster"
    return "ENPC Supporter"
