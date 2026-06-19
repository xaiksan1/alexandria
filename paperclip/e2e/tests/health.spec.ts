import { test, expect } from "@playwright/test";

test.describe("Health endpoint", () => {
  test("returns ok status", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
  });

  test("returns deployment mode", async ({ request }) => {
    const res = await request.get("/api/health");
    const body = await res.json();
    expect(["local_trusted", "authenticated"]).toContain(body.deploymentMode);
  });

  test("returns deployment exposure", async ({ request }) => {
    const res = await request.get("/api/health");
    const body = await res.json();
    expect(["private", "public"]).toContain(body.deploymentExposure);
  });

  test("returns authReady flag", async ({ request }) => {
    const res = await request.get("/api/health");
    const body = await res.json();
    expect(typeof body.authReady).toBe("boolean");
  });
});
