from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from paylater.db.models import InstallmentRow, PaymentRow, PlanRow
from paylater.domain.markets import MarketCode
from paylater.domain.money import Currency
from paylater.domain.plans import Installment, Plan, PlanStatus


def _to_domain(row: PlanRow) -> Plan:
    return Plan(
        plan_id=row.plan_id,
        market=MarketCode(row.market),
        currency=Currency(row.currency),
        principal=row.principal,
        apr=row.apr,
        term=row.term,
        created_at=row.created_at,
        status=PlanStatus(row.status),
        installments=[
            Installment(item.sequence, item.due_date, item.amount, item.paid)
            for item in row.installments
        ],
    )


class PlanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, plan: Plan) -> None:
        self._session.add(
            PlanRow(
                plan_id=plan.plan_id,
                market=plan.market.value,
                currency=plan.currency.value,
                principal=plan.principal,
                apr=plan.apr,
                term=plan.term,
                status=plan.status.value,
                created_at=plan.created_at,
                installments=[
                    InstallmentRow(
                        sequence=item.sequence,
                        due_date=item.due_date,
                        amount=item.amount,
                        paid=item.paid,
                    )
                    for item in plan.installments
                ],
            )
        )

    def get(self, plan_id: str, *, for_update: bool = False) -> Plan | None:
        statement = select(PlanRow).where(PlanRow.plan_id == plan_id)
        if for_update:
            statement = statement.with_for_update()
        row = self._session.scalars(statement).one_or_none()
        return _to_domain(row) if row else None

    def save(self, plan: Plan) -> None:
        row = self._session.get_one(PlanRow, plan.plan_id)
        row.status = plan.status.value
        paid_by_sequence = {item.sequence: item.paid for item in plan.installments}
        for item in row.installments:
            item.paid = paid_by_sequence[item.sequence]

    def find_payment(self, plan_id: str, idempotency_key: str) -> PaymentRow | None:
        return self._session.scalars(
            select(PaymentRow).where(
                PaymentRow.plan_id == plan_id, PaymentRow.idempotency_key == idempotency_key
            )
        ).one_or_none()

    def add_payment(self, payment: PaymentRow) -> None:
        self._session.add(payment)
