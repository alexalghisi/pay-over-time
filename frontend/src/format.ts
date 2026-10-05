import type { Currency, MarketCode } from "./api";

export const MARKET_LOCALE: Record<MarketCode, string> = { GB: "en-GB", CA: "en-CA" };
export const MARKET_CURRENCY: Record<MarketCode, Currency> = { GB: "GBP", CA: "CAD" };

export function formatMoney(amount: string, market: MarketCode): string {
    return new Intl.NumberFormat(MARKET_LOCALE[market], {
        style: "currency",
        currency: MARKET_CURRENCY[market],
    }).format(Number(amount));
}

export function formatApr(apr: string): string {
    const percent = Number(apr) * 100;
    return percent === 0 ? "0% APR" : `${percent.toFixed(2).replace(/\.?0+$/, "")}% APR`;
}

export function formatDueDate(isoDate: string, market: MarketCode): string {
    return new Intl.DateTimeFormat(MARKET_LOCALE[market], {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
    }).format(new Date(`${isoDate}T00:00:00Z`));
}
