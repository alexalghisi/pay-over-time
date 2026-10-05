export type MarketCode = "GB" | "CA";
export type Currency = "GBP" | "CAD";

export interface Installment {
    sequence: number;
    due_date: string;
    amount: string;
    paid: string;
}

export interface Offer {
    term: number;
    apr: string;
    monthly_payment: string;
    total_interest: string;
    total_payable: string;
    schedule: Installment[];
}

export interface Quote {
    market: MarketCode;
    currency: Currency;
    amount: string;
    offers: Offer[];
}

export interface Plan {
    plan_id: string;
    market: MarketCode;
    currency: Currency;
    principal: string;
    apr: string;
    term: number;
    status: "active" | "paid_off";
    outstanding: string;
    installments: Installment[];
}

export interface PayLaterApi {
    quote(market: MarketCode, amount: string, signal?: AbortSignal): Promise<Quote>;
    createPlan(market: MarketCode, amount: string, term: number): Promise<Plan>;
}

export class ApiError extends Error {
    constructor(
        readonly code: string,
        message: string,
    ) {
        super(message);
        this.name = "ApiError";
    }
}

async function post<T>(baseUrl: string, path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        ...(signal ? { signal } : {}),
    });
    const payload: unknown = await response.json().catch(() => undefined);
    if (!response.ok) {
        const error = (payload as { error?: { code: string; message: string } } | undefined)?.error;
        throw new ApiError(error?.code ?? "unexpected", error?.message ?? "Something went wrong. Please try again.");
    }
    return payload as T;
}

export function createApi(baseUrl: string): PayLaterApi {
    return {
        quote: (market, amount, signal) => post<Quote>(baseUrl, "/v1/quotes", { market, amount }, signal),
        createPlan: (market, amount, term) => post<Plan>(baseUrl, "/v1/plans", { market, amount, term }),
    };
}
