import { type Page, request as playwrightRequest } from "@playwright/test";

export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@paperclip.e2e";
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "AdminP@ss123!";
export const ADMIN_NAME = "E2E Admin";

export async function signUp(page: Page, email: string, password: string, name: string) {
  await page.goto("/auth");
  try {
    await page.getByRole("link", { name: /sign up/i }).click({ timeout: 2_000 });
  } catch {
    await page.getByText(/sign up/i).click();
  }
  await page.getByLabel(/name/i).fill(name);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).first().fill(password);
  await page.getByRole("button", { name: /sign up/i }).click();
  await page.waitForURL(/^(?!.*\/auth).*$/, { timeout: 15_000 });
}

export async function signIn(page: Page, email: string, password: string) {
  await page.goto("/auth");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/^(?!.*\/auth).*$/, { timeout: 15_000 });
}

export async function signOut(page: Page) {
  await page.getByRole("button", { name: /sign out|logout/i }).click().catch(async () => {
    await page.getByRole("menuitem", { name: /sign out|logout/i }).click();
  });
  await page.waitForURL(/\/auth/);
}
