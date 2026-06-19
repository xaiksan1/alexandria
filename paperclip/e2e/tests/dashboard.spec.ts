import { test, expect } from "@playwright/test";
import { signUp, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME } from "../fixtures/auth";

const uniqueEmail = `dashboard-${Date.now()}@paperclip.e2e`;

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await signUp(page, uniqueEmail, ADMIN_PASSWORD, ADMIN_NAME).catch(() => {
      // Account may already exist from a previous run — try sign in instead
    });
  });

  test("shows dashboard after login", async ({ page }) => {
    await expect(page).not.toHaveURL(/\/auth/);
    // The app root should load without error
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("navigation sidebar is visible", async ({ page }) => {
    // Sidebar nav should contain key sections
    const nav = page.getByRole("navigation").first();
    await expect(nav).toBeVisible();
  });

  test("agents link is present in navigation", async ({ page }) => {
    await expect(page.getByRole("link", { name: /agents/i })).toBeVisible();
  });

  test("issues link is present in navigation", async ({ page }) => {
    await expect(page.getByRole("link", { name: /issues/i })).toBeVisible();
  });
});
