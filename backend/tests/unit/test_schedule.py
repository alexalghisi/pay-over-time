from datetime import date
from decimal import Decimal

import pytest

from paylater.domain.schedule import build_schedule

START = date(2026, 2, 1)


def test_zero_apr_puts_rounding_remainder_on_first_installment() -> None:
    schedule = build_schedule(Decimal("100.00"), Decimal("0"), 3, START)
    assert [row.amount for row in schedule] == [
        Decimal("33.34"),
        Decimal("33.33"),
        Decimal("33.33"),
    ]
    assert all(row.interest == 0 for row in schedule)


def test_amortised_schedule_matches_annuity_payment() -> None:
    schedule = build_schedule(Decimal("1200.00"), Decimal("0.199"), 12, START)
    assert schedule[0].amount == Decimal("111.10")
    assert schedule[0].interest == Decimal("19.90")
    assert schedule[-1].amount == Decimal("111.15")
    assert [row.due_date for row in schedule[:3]] == [
        date(2026, 3, 1),
        date(2026, 4, 1),
        date(2026, 5, 1),
    ]


@pytest.mark.parametrize("principal", ["30.00", "99.99", "1234.56", "5000.00", "9999.99"])
@pytest.mark.parametrize(("apr", "term"), [("0", 3), ("0.099", 6), ("0.1499", 12), ("0.1999", 24)])
def test_principal_is_repaid_to_the_cent(principal: str, apr: str, term: int) -> None:
    schedule = build_schedule(Decimal(principal), Decimal(apr), term, START)
    assert len(schedule) == term
    assert sum(row.principal for row in schedule) == Decimal(principal)
    assert all(row.amount == row.principal + row.interest for row in schedule)
    assert all(row.amount == row.amount.quantize(Decimal("0.01")) for row in schedule)
    regular = {row.amount for row in schedule[1:-1]} if Decimal(apr) else set()
    assert len(regular) <= 1


@pytest.mark.parametrize(
    ("principal", "apr", "term"),
    [
        ("0", "0.1", 3),
        ("-5.00", "0.1", 3),
        ("10.005", "0.1", 3),
        ("10.00", "-0.1", 3),
        ("10.00", "0.1", 0),
    ],
)
def test_rejects_invalid_input(principal: str, apr: str, term: int) -> None:
    with pytest.raises(ValueError):
        build_schedule(Decimal(principal), Decimal(apr), term, START)


def test_due_dates_stay_anchored_to_the_start_day() -> None:
    schedule = build_schedule(Decimal("90.00"), Decimal("0"), 3, date(2026, 1, 31))
    assert [row.due_date for row in schedule] == [
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]
