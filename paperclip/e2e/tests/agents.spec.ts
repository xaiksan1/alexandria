import { test, expect } from "@playwright/test";
import { signUp, ADMIN_PASSWORD, ADMIN_NAME } from "../fixtures/auth";

const uniqueEmail = `agents-${Date.now()}@paperclip.e2e`;

test.describe("Agents page (authenticated)", () => {
  test.beforeEach(async ({ page }) => {
    await signUp(page, uniqueEmail, ADMIN_PASSWORD, ADMIN_NAME).catch(() => {});
    await page.getByRole("link", { name: /agents/i }).click();
    await page.waitForURL(/\/agents/);
  });

  test("renders agents page", async ({ page }) => {
    await expect(page).toHaveURL(/\/agents/);
  });

  test("shows empty state or agent list", async ({ page }) => {
    const hasAgents = await page.getByRole("link", { name: /agent/i }).count() > 0;
    const hasEmpty = await page.getByText(/no agents|get started|create/i).count() > 0;
    expect(hasAgents || hasEmpty).toBeTruthy();
  });

  test("has a button to create a new agent", async ({ page }) => {
    const createBtn = page.getByRole("button", { name: /new agent|create agent|\+/i });
    const createLink = page.getByRole("link", { name: /new agent|create agent/i });
    const visible = (await createBtn.count()) > 0 || (await createLink.count()) > 0;
    expect(visible).toBeTruthy();
  });
});

test.describe("Agents API (unauthenticated)", () => {
  test("GET /api/agents requires auth", async ({ request }) => {
    const res = await request.get("/api/agents");
    expect([401, 403, 302]).toContain(res.status());
  });
});
