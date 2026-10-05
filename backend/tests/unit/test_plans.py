from datetime import date, datetime
from decimal import Decimal

import pytest

from paylater.domain.errors import InvalidPayment
from paylater.domain.markets import MARKETS, MarketCode
from paylater.domain.money import Currency
from paylater.domain.offers import build_offer
from paylater.domain.plans import Allocation, Plan, PlanStatus


@pytest.fixture
def plan() -> Plan:
    offer = build_offer(MARKETS[MarketCode.GB], Decimal("100.00"), 3, date(2026, 1, 31))
    return Plan.from_offer(
        "plan_1", MarketCode.GB, Currency.GBP, Decimal("100.00"), offer, datetime(2026, 1, 31)
    )


def test_allocates_payment_to_oldest_installments_first(plan: Plan) -> None:
    allocations = plan.apply_payment(Decimal("50.00"))
    assert allocations == [Allocation(1, Decimal("33.34")), Allocation(2, Decimal("16.66"))]
    assert plan.outstanding == Decimal("50.00")
    next_due = plan.next_due()
    assert next_due is not None
    assert next_due.sequence == 2


def test_marks_plan_paid_off_when_balance_reaches_zero(plan: Plan) -> None:
    plan.apply_payment(Decimal("100.00"))
    assert plan.status is PlanStatus.PAID_OFF
    assert plan.next_due() is None


@pytest.mark.parametrize("amount", ["0", "-1.00", "10.001", "100.01"])
def test_rejects_invalid_amounts(plan: Plan, amount: str) -> None:
    with pytest.raises(InvalidPayment):
        plan.apply_payment(Decimal(amount))
    assert plan.outstanding == Decimal("100.00")


def test_rejects_payments_on_paid_off_plan(plan: Plan) -> None:
    plan.apply_payment(Decimal("100.00"))
    with pytest.raises(InvalidPayment, match="already paid off"):
        plan.apply_payment(Decimal("1.00"))
