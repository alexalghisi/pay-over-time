import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError, type PayLaterApi, type Plan, type Quote } from "../api";
import { Checkout } from "./Checkout";

const QUOTE: Quote = {
    market: "GB",
    currency: "GBP",
    amount: "300.00",
    offers: [
        {
            term: 3,
            apr: "0.0000",
            monthly_payment: "100.00",
            total_interest: "0.00",
            total_payable: "300.00",
            schedule: [1, 2, 3].map((sequence) => ({
                sequence,
                due_date: `2026-0${sequence + 1}-28`,
                amount: "100.00",
                paid: "0.00",
            })),
        },
        {
            term: 6,
            apr: "0.0990",
            monthly_payment: "51.46",
            total_interest: "8.76",
            total_payable: "308.76",
            schedule: [1, 2, 3, 4, 5, 6].map((sequence) => ({
                sequence,
                due_date: `2026-0${sequence + 1}-28`,
                amount: "51.46",
                paid: "0.00",
            })),
        },
    ],
};

const PLAN: Plan = {
    plan_id: "plan_123",
    market: "GB",
    currency: "GBP",
    principal: "300.00",
    apr: "0.0990",
    term: 6,
    status: "active",
    outstanding: "308.76",
    installments: QUOTE.offers[1]!.schedule,
};

function fakeApi(overrides: Partial<PayLaterApi> = {}): PayLaterApi {
    return {
        quote: vi.fn().mockResolvedValue(QUOTE),
        createPlan: vi.fn().mockResolvedValue(PLAN),
        ...overrides,
    };
}

describe("Checkout", () => {
    it("shows offers for the basket and preselects the first one", async () => {
        render(<Checkout api={fakeApi()} initialAmount="300.00" debounceMs={0} />);

        const options = await screen.findAllByRole("radio");
        expect(options).toHaveLength(2);
        expect(options[0]).toBeChecked();
        expect(screen.getByText("3 monthly payments, total £300.00")).toBeInTheDocument();
    });

    it("updates the schedule when another plan is chosen", async () => {
        const user = userEvent.setup();
        render(<Checkout api={fakeApi()} initialAmount="300.00" debounceMs={0} />);

        await user.click(await screen.findByRole("radio", { name: /6 months/ }));

        const table = screen.getByRole("table", { name: /6 monthly payments/ });
        expect(within(table).getAllByRole("row")).toHaveLength(7);
        expect(screen.getByText("9.9% APR")).toBeInTheDocument();
    });

    it("re-quotes in the selected market", async () => {
        const api = fakeApi();
        const user = userEvent.setup();
        render(<Checkout api={api} initialAmount="300.00" debounceMs={0} />);

        await user.selectOptions(screen.getByRole("combobox"), "CA");

        await waitFor(() => expect(api.quote).toHaveBeenLastCalledWith("CA", "300.00", expect.any(AbortSignal)));
    });

    it("does not quote an invalid amount", async () => {
        const api = fakeApi();
        const user = userEvent.setup();
        render(<Checkout api={api} initialAmount="300.00" debounceMs={0} />);
        await screen.findAllByRole("radio");

        const input = screen.getByRole("textbox", { name: "Basket total" });
        await user.clear(input);
        await user.type(input, "12.345");

        expect(await screen.findByText("Enter an amount like 1240.00")).toBeInTheDocument();
        expect(screen.queryAllByRole("radio")).toHaveLength(0);
        expect(api.quote).not.toHaveBeenCalledWith("GB", "12.345", expect.anything());
    });

    it("confirms the selected plan using the quoted amount", async () => {
        const api = fakeApi();
        const user = userEvent.setup();
        render(<Checkout api={api} initialAmount="300.00" debounceMs={0} />);

        await user.click(await screen.findByRole("radio", { name: /6 months/ }));
        await user.click(screen.getByRole("button", { name: "Confirm plan" }));

        expect(api.createPlan).toHaveBeenCalledWith("GB", "300.00", 6);
        expect(await screen.findByRole("heading", { name: "You're all set" })).toBeInTheDocument();
        expect(screen.getByText("plan_123")).toBeInTheDocument();
    });

    it("explains why a basket cannot be split", async () => {
        const api = fakeApi({
            quote: vi.fn().mockRejectedValue(new ApiError("amount_out_of_range", "GB accepts 30.00-5000.00 GBP")),
        });
        render(<Checkout api={api} initialAmount="9000.00" debounceMs={0} />);

        expect(await screen.findByRole("alert")).toHaveTextContent("GB accepts 30.00-5000.00 GBP");
        expect(screen.queryByRole("button", { name: "Confirm plan" })).not.toBeInTheDocument();
    });
});
