import { test as setup, expect } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const authFile = path.join(import.meta.dirname, ".auth", "user.json");

/**
 * Global setup: authenticate via API and store token for reuse.
 *
 * Expects the API server at localhost:8001 with a seeded user.
 * Default credentials from the project handoff: admin / admin123456
 */
setup("authenticate", async ({ request }) => {
  const loginUrl = "http://localhost:8001/api/v1/auth/login";

  const resp = await request.post(loginUrl, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    data: "username=admin&password=admin123456",
  });

  expect(resp.ok(), `Login failed: ${await resp.text()}`).toBeTruthy();

  const { access_token } = await resp.json();
  expect(access_token).toBeTruthy();

  // Write storageState-compatible auth file with the token in localStorage
  const authState = {
    cookies: [],
    origins: [
      {
        origin: "http://localhost:5175",
        localStorage: [{ name: "token", value: access_token }],
      },
    ],
  };

  fs.mkdirSync(path.dirname(authFile), { recursive: true });
  fs.writeFileSync(authFile, JSON.stringify(authState, null, 2));
});
