from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType

from paylater.domain.money import Currency


class MarketCode(StrEnum):
    GB = "GB"
    CA = "CA"


@dataclass(frozen=True)
class Market:
    code: MarketCode
    currency: Currency
    locale: str
    min_amount: Decimal
    max_amount: Decimal
    apr_by_term: MappingProxyType[int, Decimal]

    def accepts(self, amount: Decimal) -> bool:
        return self.min_amount <= amount <= self.max_amount


MARKETS: MappingProxyType[MarketCode, Market] = MappingProxyType(
    {
        MarketCode.GB: Market(
            code=MarketCode.GB,
            currency=Currency.GBP,
            locale="en-GB",
            min_amount=Decimal("30.00"),
            max_amount=Decimal("5000.00"),
            apr_by_term=MappingProxyType(
                {3: Decimal("0.0000"), 6: Decimal("0.0990"), 12: Decimal("0.1990")}
            ),
        ),
        MarketCode.CA: Market(
            code=MarketCode.CA,
            currency=Currency.CAD,
            locale="en-CA",
            min_amount=Decimal("50.00"),
            max_amount=Decimal("10000.00"),
            apr_by_term=MappingProxyType(
                {
                    3: Decimal("0.0000"),
                    6: Decimal("0.0999"),
                    12: Decimal("0.1499"),
                    24: Decimal("0.1999"),
                }
            ),
        ),
    }
)
