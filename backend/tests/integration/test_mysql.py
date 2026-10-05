import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from paylater.db.models import Base
from paylater.domain.markets import MarketCode
from paylater.service import PayLaterService

MYSQL_URL = os.environ.get("PAYLATER_TEST_MYSQL_URL")

pytestmark = pytest.mark.skipif(not MYSQL_URL, reason="PAYLATER_TEST_MYSQL_URL is not set")


@pytest.fixture
def service() -> PayLaterService:
    assert MYSQL_URL
    engine = create_engine(MYSQL_URL, pool_size=10)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return PayLaterService(
        sessionmaker(engine, expire_on_commit=False), clock=lambda: datetime(2026, 1, 31, 9, 30)
    )


def test_concurrent_retries_record_a_single_payment(service: PayLaterService) -> None:
    plan = service.create_plan(MarketCode.CA, Decimal("300.00"), 3)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: service.pay(plan.plan_id, Decimal("100.00"), "mobile-retry-1"), range(8)
            )
        )

    assert len({result.payment_id for result in results}) == 1
    assert sum(not result.replayed for result in results) == 1
    assert service.get_plan(plan.plan_id).outstanding == Decimal("200.00")


def test_concurrent_distinct_payments_never_overpay(service: PayLaterService) -> None:
    plan = service.create_plan(MarketCode.CA, Decimal("300.00"), 3)

    def attempt(index: int) -> bool:
        try:
            service.pay(plan.plan_id, Decimal("100.00"), f"distinct-{index}")
        except Exception:
            return False
        return True

    with ThreadPoolExecutor(max_workers=6) as pool:
        succeeded = sum(pool.map(attempt, range(6)))

    assert succeeded == 3
    assert service.get_plan(plan.plan_id).outstanding == Decimal("0.00")
