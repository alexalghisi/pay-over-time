import { describe, expect, it } from "vitest";

import { formatApr, formatDueDate, formatMoney } from "./format";

describe("formatting", () => {
    it("formats money in the market's currency and locale", () => {
        expect(formatMoney("1240.5", "GB")).toBe("£1,240.50");
        expect(formatMoney("99", "CA")).toBe("$99.00");
    });

    it.each([
        ["0.0000", "0% APR"],
        ["0.0990", "9.9% APR"],
        ["0.1499", "14.99% APR"],
        ["0.2000", "20% APR"],
    ])("formats APR %s as %s", (apr, expected) => {
        expect(formatApr(apr)).toBe(expected);
    });

    it("formats due dates without shifting the day across time zones", () => {
        expect(formatDueDate("2026-02-28", "GB")).toBe("28 Feb 2026");
    });
});
