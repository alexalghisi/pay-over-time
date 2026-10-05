from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

CENT = Decimal("0.01")


class Currency(StrEnum):
    GBP = "GBP"
    CAD = "CAD"


def to_cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)
