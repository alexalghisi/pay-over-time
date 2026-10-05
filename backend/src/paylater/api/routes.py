from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response, status

from paylater.api.schemas import (
    CreatePlanRequest,
    InstallmentOut,
    OfferOut,
    PaymentOut,
    PaymentRequest,
    PlanOut,
    QuoteRequest,
    QuoteResponse,
)
from paylater.domain.markets import MARKETS
from paylater.domain.offers import Offer
from paylater.domain.plans import Plan
from paylater.service import PayLaterService

router = APIRouter(prefix="/v1")


def get_service(request: Request) -> PayLaterService:
    service: PayLaterService = request.app.state.service
    return service


Service = Annotated[PayLaterService, Depends(get_service)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]


def _offer_out(offer: Offer) -> OfferOut:
    return OfferOut(
        term=offer.term,
        apr=offer.apr,
        monthly_payment=offer.monthly_payment,
        total_interest=offer.total_interest,
        total_payable=offer.total_payable,
        schedule=[
            InstallmentOut(sequence=row.sequence, due_date=row.due_date, amount=row.amount)
            for row in offer.schedule
        ],
    )


def _plan_out(plan: Plan) -> PlanOut:
    return PlanOut(
        plan_id=plan.plan_id,
        market=plan.market,
        currency=plan.currency,
        principal=plan.principal,
        apr=plan.apr,
        term=plan.term,
        status=plan.status,
        outstanding=plan.outstanding,
        installments=[
            InstallmentOut(
                sequence=item.sequence, due_date=item.due_date, amount=item.amount, paid=item.paid
            )
            for item in plan.installments
        ],
    )


@router.post("/quotes", response_model=QuoteResponse)
def create_quote(body: QuoteRequest, service: Service) -> QuoteResponse:
    offers = service.quote(body.market, body.amount)
    return QuoteResponse(
        market=body.market,
        currency=MARKETS[body.market].currency,
        amount=body.amount,
        offers=[_offer_out(offer) for offer in offers],
    )


@router.post("/plans", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(body: CreatePlanRequest, service: Service) -> PlanOut:
    return _plan_out(service.create_plan(body.market, body.amount, body.term))


@router.get("/plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: str, service: Service) -> PlanOut:
    return _plan_out(service.get_plan(plan_id))


@router.post(
    "/plans/{plan_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED
)
def pay(
    plan_id: str,
    body: PaymentRequest,
    idempotency_key: IdempotencyKey,
    response: Response,
    service: Service,
) -> PaymentOut:
    result = service.pay(plan_id, body.amount, idempotency_key)
    if result.replayed:
        response.status_code = status.HTTP_200_OK
    return PaymentOut(
        payment_id=result.payment_id, amount=result.amount, plan=_plan_out(result.plan)
    )
