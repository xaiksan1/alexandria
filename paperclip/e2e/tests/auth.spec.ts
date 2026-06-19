import { test, expect } from "@playwright/test";

const TEST_EMAIL = `e2e-test-${Date.now()}@paperclip.test`;
const TEST_PASSWORD = "E2eTestP@ss123!";
const TEST_NAME = "E2E Test User";

test.describe("Auth — unauthenticated redirects", () => {
  test("redirects / to /auth when not logged in", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL(/\/auth/);
    await expect(page).toHaveURL(/\/auth/);
  });

  test("redirects /agents to /auth when not logged in", async ({ page }) => {
    await page.goto("/agents");
    await page.waitForURL(/\/auth/);
    await expect(page).toHaveURL(/\/auth/);
  });

  test("shows sign in form on /auth", async ({ page }) => {
    await page.goto("/auth");
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });
});

test.describe("Auth — sign up flow", () => {
  test("can create a new account", async ({ page }) => {
    await page.goto("/auth");

    await page.getByRole("link", { name: /sign up/i }).click().catch(() =>
      page.getByText(/sign up/i).click()
    );

    await page.getByLabel(/name/i).fill(TEST_NAME);
    await page.getByLabel(/email/i).fill(TEST_EMAIL);
    const passwordFields = page.getByLabel(/password/i);
    await passwordFields.first().fill(TEST_PASSWORD);

    await page.getByRole("button", { name: /sign up/i }).click();

    await page.waitForURL(/^(?!.*\/auth).*$/, { timeout: 15_000 });
    await expect(page).not.toHaveURL(/\/auth/);
  });
});

test.describe("Auth — sign in flow", () => {
  test("shows error on wrong password", async ({ page }) => {
    await page.goto("/auth");

    await page.getByLabel(/email/i).fill("wrong@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await expect(page.getByText(/invalid|incorrect|error/i)).toBeVisible({ timeout: 5_000 });
  });
});

test.describe("Auth API", () => {
  test("GET /api/auth/get-session returns null when unauthenticated", async ({ request }) => {
    const res = await request.get("/api/auth/get-session");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body).toBeNull();
  });
});
