from datetime import date
from decimal import Decimal

import pytest

from paylater.domain.errors import AmountOutOfRange, UnsupportedTerm
from paylater.domain.markets import MARKETS, MarketCode
from paylater.domain.offers import build_offer, quote

TODAY = date(2026, 1, 31)


def test_quote_returns_one_offer_per_market_term() -> None:
    offers = quote(MARKETS[MarketCode.CA], Decimal("600.00"), TODAY)
    assert [offer.term for offer in offers] == [3, 6, 12, 24]


def test_interest_free_offer_costs_exactly_the_purchase_price() -> None:
    offer = build_offer(MARKETS[MarketCode.GB], Decimal("250.00"), 3, TODAY)
    assert offer.total_interest == 0
    assert offer.total_payable == Decimal("250.00")
    assert offer.monthly_payment == Decimal("83.33")
    assert offer.schedule[0].due_date == date(2026, 2, 28)


def test_interest_bearing_offer_reports_totals() -> None:
    offer = build_offer(MARKETS[MarketCode.GB], Decimal("1200.00"), 12, TODAY)
    assert offer.total_payable == offer.total_interest + Decimal("1200.00")
    assert offer.total_payable == sum(row.amount for row in offer.schedule)
    assert offer.total_interest > 0


@pytest.mark.parametrize("amount", ["29.99", "5000.01"])
def test_rejects_amounts_outside_market_limits(amount: str) -> None:
    with pytest.raises(AmountOutOfRange, match=r"30\.00-5000\.00 GBP"):
        build_offer(MARKETS[MarketCode.GB], Decimal(amount), 3, TODAY)


def test_rejects_terms_the_market_does_not_offer() -> None:
    with pytest.raises(UnsupportedTerm, match="GB does not offer a 24-month plan"):
        build_offer(MARKETS[MarketCode.GB], Decimal("500.00"), 24, TODAY)
