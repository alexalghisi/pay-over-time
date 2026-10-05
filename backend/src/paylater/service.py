from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from paylater.db.models import PaymentRow
from paylater.db.repository import PlanRepository
from paylater.domain.errors import InvalidPayment, PlanNotFound
from paylater.domain.markets import MARKETS, MarketCode
from paylater.domain.offers import Offer, build_offer, quote
from paylater.domain.plans import Plan

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


@dataclass(frozen=True)
class PaymentResult:
    payment_id: str
    amount: Decimal
    plan: Plan
    replayed: bool


class PayLaterService:
    def __init__(self, session_factory: Callable[[], Session], clock: Clock = utc_now) -> None:
        self._session_factory = session_factory
        self._clock = clock

    @contextmanager
    def _repository(self) -> Iterator[tuple[Session, PlanRepository]]:
        with self._session_factory() as session:
            yield session, PlanRepository(session)

    def _today(self) -> date:
        return self._clock().date()

    def quote(self, market: MarketCode, amount: Decimal) -> list[Offer]:
        return quote(MARKETS[market], amount, self._today())

    def create_plan(self, market: MarketCode, amount: Decimal, term: int) -> Plan:
        rules = MARKETS[market]
        offer = build_offer(rules, amount, term, self._today())
        plan = Plan.from_offer(new_id("plan"), market, rules.currency, amount, offer, self._clock())
        with self._repository() as (session, plans):
            plans.add(plan)
            session.commit()
        return plan

    def get_plan(self, plan_id: str) -> Plan:
        with self._repository() as (_, plans):
            plan = plans.get(plan_id)
        if plan is None:
            raise PlanNotFound(f"Plan {plan_id} not found")
        return plan

    def pay(self, plan_id: str, amount: Decimal, idempotency_key: str) -> PaymentResult:
        try:
            return self._apply_payment(plan_id, amount, idempotency_key)
        except IntegrityError:
            return self._apply_payment(plan_id, amount, idempotency_key)

    def _apply_payment(self, plan_id: str, amount: Decimal, idempotency_key: str) -> PaymentResult:
        with self._repository() as (session, plans):
            plan = plans.get(plan_id, for_update=True)
            if plan is None:
                raise PlanNotFound(f"Plan {plan_id} not found")
            existing = plans.find_payment(plan_id, idempotency_key)
            if existing is not None:
                if existing.amount != amount:
                    raise InvalidPayment("Idempotency key was already used for a different amount")
                return PaymentResult(existing.payment_id, existing.amount, plan, replayed=True)
            plan.apply_payment(amount)
            plans.save(plan)
            payment = PaymentRow(
                payment_id=new_id("pay"),
                plan_id=plan_id,
                idempotency_key=idempotency_key,
                amount=amount,
                created_at=self._clock(),
            )
            plans.add_payment(payment)
            session.commit()
            return PaymentResult(payment.payment_id, amount, plan, replayed=False)
