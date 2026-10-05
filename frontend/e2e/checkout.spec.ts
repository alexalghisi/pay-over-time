import { expect, test } from "@playwright/test";

test("customer splits a UK basket into six payments", async ({ page }) => {
    await page.goto("/");

    const offers = page.getByRole("radio");
    await expect(offers).toHaveCount(3);

    await page.getByRole("radio", { name: /6 months/ }).check();
    const schedule = page.getByRole("table", { name: /6 monthly payments/ });
    await expect(schedule.getByRole("row")).toHaveCount(7);

    await page.getByRole("button", { name: "Confirm plan" }).click();

    await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible();
    await expect(page.getByText(/^Plan plan_/)).toContainText("6 payments, 9.9% APR");
});

test("Canadian customers see CAD offers including 24 months", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("combobox").selectOption("CA");

    await expect(page.getByRole("radio")).toHaveCount(4);
    await expect(page.getByRole("radio", { name: /24 months/ })).toBeVisible();
    await expect(page.getByText(/Total \$1,240\.00/)).toBeVisible();
});

test("baskets above the market limit explain why they cannot be split", async ({ page }) => {
    await page.goto("/");

    const amount = page.getByRole("textbox", { name: "Basket total" });
    await amount.fill("9000.00");

    await expect(page.getByRole("alert")).toContainText("GB accepts 30.00-5000.00 GBP");
    await expect(page.getByRole("button", { name: "Confirm plan" })).toHaveCount(0);
});
