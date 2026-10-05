import { useEffect, useState, type FormEvent } from "react";

import { ApiError, type MarketCode, type PayLaterApi, type Plan, type Quote } from "../api";
import { formatApr, formatMoney } from "../format";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { OfferList } from "./OfferList";
import { ScheduleTable } from "./ScheduleTable";

interface CheckoutProps {
    api: PayLaterApi;
    initialAmount: string;
    debounceMs?: number;
}

const AMOUNT_PATTERN = /^\d+(\.\d{1,2})?$/;

type Status = "idle" | "loading" | "submitting";

function errorMessage(error: unknown): string {
    return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

export function Checkout({ api, initialAmount, debounceMs = 300 }: CheckoutProps) {
    const [market, setMarket] = useState<MarketCode>("GB");
    const [amount, setAmount] = useState(initialAmount);
    const [quote, setQuote] = useState<Quote | null>(null);
    const [selectedTerm, setSelectedTerm] = useState<number | null>(null);
    const [plan, setPlan] = useState<Plan | null>(null);
    const [status, setStatus] = useState<Status>("idle");
    const [error, setError] = useState<string | null>(null);

    const debouncedAmount = useDebouncedValue(amount, debounceMs);
    const amountIsValid = AMOUNT_PATTERN.test(debouncedAmount);

    useEffect(() => {
        if (!amountIsValid) {
            setQuote(null);
            return;
        }
        const controller = new AbortController();
        setStatus("loading");
        setError(null);
        api.quote(market, debouncedAmount, controller.signal)
            .then((result) => {
                if (controller.signal.aborted) {
                    return;
                }
                setQuote(result);
                setSelectedTerm(result.offers[0]?.term ?? null);
                setStatus("idle");
            })
            .catch((caught: unknown) => {
                if (controller.signal.aborted) {
                    return;
                }
                setQuote(null);
                setError(errorMessage(caught));
                setStatus("idle");
            });
        return () => controller.abort();
    }, [api, market, debouncedAmount, amountIsValid]);

    const selectedOffer = quote?.offers.find((offer) => offer.term === selectedTerm) ?? null;

    async function confirm(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!quote || !selectedOffer) {
            return;
        }
        setStatus("submitting");
        setError(null);
        try {
            setPlan(await api.createPlan(quote.market, quote.amount, selectedOffer.term));
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setStatus("idle");
        }
    }

    if (plan) {
        return (
            <section className="card confirmation" aria-labelledby="confirmation-title">
                <h2 id="confirmation-title">You're all set</h2>
                <p>
                    Plan <code>{plan.plan_id}</code>: {plan.term} payments, {formatApr(plan.apr)}.
                </p>
                <ScheduleTable market={plan.market} installments={plan.installments} caption="Your payment schedule" />
            </section>
        );
    }

    return (
        <form className="card" onSubmit={confirm} aria-busy={status !== "idle"}>
            <div className="controls">
                <label>
                    Country
                    <select value={market} onChange={(event) => setMarket(event.target.value as MarketCode)}>
                        <option value="GB">United Kingdom (GBP)</option>
                        <option value="CA">Canada (CAD)</option>
                    </select>
                </label>
                <label>
                    Basket total
                    <input
                        inputMode="decimal"
                        value={amount}
                        onChange={(event) => setAmount(event.target.value)}
                        aria-describedby="amount-hint"
                    />
                </label>
            </div>
            <p id="amount-hint" className={amountIsValid ? "hint" : "hint hint--invalid"}>
                {amountIsValid ? "Plans update as you type." : "Enter an amount like 1240.00"}
            </p>

            <div aria-live="polite">
                {error && (
                    <p role="alert" className="error">
                        {error}
                    </p>
                )}
                {status === "loading" && !quote && <p className="hint">Finding plans…</p>}
            </div>

            {quote && (
                <>
                    <OfferList
                        market={quote.market}
                        offers={quote.offers}
                        selectedTerm={selectedTerm}
                        onSelect={setSelectedTerm}
                    />
                    {selectedOffer && (
                        <ScheduleTable
                            market={quote.market}
                            installments={selectedOffer.schedule}
                            caption={`${selectedOffer.term} monthly payments, total ${formatMoney(selectedOffer.total_payable, quote.market)}`}
                        />
                    )}
                    <button type="submit" disabled={!selectedOffer || status === "submitting"}>
                        {status === "submitting" ? "Confirming…" : "Confirm plan"}
                    </button>
                </>
            )}
        </form>
    );
}
