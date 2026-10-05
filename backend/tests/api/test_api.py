from fastapi.testclient import TestClient


def create_plan(client: TestClient, amount: str = "100.00", term: int = 3) -> dict[str, object]:
    response = client.post("/v1/plans", json={"market": "GB", "amount": amount, "term": term})
    assert response.status_code == 201
    body: dict[str, object] = response.json()
    return body


def test_quote_lists_offers_for_market(client: TestClient) -> None:
    response = client.post("/v1/quotes", json={"market": "CA", "amount": "600.00"})
    body = response.json()
    assert response.status_code == 200
    assert body["currency"] == "CAD"
    assert [offer["term"] for offer in body["offers"]] == [3, 6, 12, 24]
    assert body["offers"][0]["total_payable"] == "600.00"


def test_quote_rejects_amount_outside_market_limits(client: TestClient) -> None:
    response = client.post("/v1/quotes", json={"market": "GB", "amount": "10000.00"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "amount_out_of_range"


def test_quote_validates_money_precision(client: TestClient) -> None:
    response = client.post("/v1/quotes", json={"market": "GB", "amount": "100.001"})
    assert response.status_code == 422


def test_creates_and_reads_plan(client: TestClient) -> None:
    plan = create_plan(client)
    assert plan["status"] == "active"
    assert plan["outstanding"] == "100.00"
    fetched = client.get(f"/v1/plans/{plan['plan_id']}").json()
    assert fetched == plan


def test_unknown_plan_returns_404(client: TestClient) -> None:
    response = client.get("/v1/plans/plan_missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "plan_not_found"


def test_payment_is_idempotent(client: TestClient) -> None:
    plan = create_plan(client)
    url = f"/v1/plans/{plan['plan_id']}/payments"
    headers = {"Idempotency-Key": "checkout-7781-pay-1"}

    first = client.post(url, json={"amount": "40.00"}, headers=headers)
    retry = client.post(url, json={"amount": "40.00"}, headers=headers)

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["payment_id"] == first.json()["payment_id"]
    assert client.get(f"/v1/plans/{plan['plan_id']}").json()["outstanding"] == "60.00"


def test_reusing_key_with_different_amount_is_rejected(client: TestClient) -> None:
    plan = create_plan(client)
    url = f"/v1/plans/{plan['plan_id']}/payments"
    headers = {"Idempotency-Key": "checkout-7781-pay-2"}
    client.post(url, json={"amount": "40.00"}, headers=headers)
    response = client.post(url, json={"amount": "41.00"}, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_payment"


def test_paying_the_full_balance_closes_the_plan(client: TestClient) -> None:
    plan = create_plan(client)
    url = f"/v1/plans/{plan['plan_id']}/payments"
    response = client.post(
        url, json={"amount": "100.00"}, headers={"Idempotency-Key": "payoff-0001"}
    )
    assert response.json()["plan"]["status"] == "paid_off"
    overpay = client.post(url, json={"amount": "1.00"}, headers={"Idempotency-Key": "payoff-0002"})
    assert overpay.status_code == 422


def test_payment_requires_idempotency_key(client: TestClient) -> None:
    plan = create_plan(client)
    response = client.post(f"/v1/plans/{plan['plan_id']}/payments", json={"amount": "10.00"})
    assert response.status_code == 422
