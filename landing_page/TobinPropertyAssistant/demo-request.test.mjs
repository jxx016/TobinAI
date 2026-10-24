import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import test from "node:test";

import handler from "./netlify/functions/demo-request.mjs";

const ORIGIN = "https://cool-cannoli-68cac9.netlify.app";

function listen() {
  const server = createServer((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (req.url === "/fail") {
        res.writeHead(500, { "content-type": "application/json" });
        res.end(JSON.stringify({ success: false, error: "nope" }));
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(
        JSON.stringify({
          success: true,
          message: "Demo request received. We'll be in touch within 24 hours!",
          echoed: JSON.parse(raw),
        }),
      );
    });
  });
  server.listen(0, "127.0.0.1");
  return server;
}

test("proxies POST to the configured upstream and keeps CORS", async () => {
  const server = listen();
  await once(server, "listening");
  const { port } = server.address();
  process.env.DEMO_REQUEST_UPSTREAM = `http://127.0.0.1:${port}/webhook/demo-request`;
  try {
    const response = await handler(
      new Request("https://cool-cannoli-68cac9.netlify.app/.netlify/functions/demo-request", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          origin: ORIGIN,
        },
        body: JSON.stringify({
          email: "ada@example.com",
          name: "Ada",
          source: "demo-request",
        }),
      }),
    );
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.equal(body.success, true);
    assert.equal(body.echoed.email, "ada@example.com");
    assert.equal(body.echoed.name, "Ada");
    assert.equal(response.headers.get("access-control-allow-origin"), ORIGIN);
  } finally {
    server.close();
  }
});

test("OPTIONS preflight allows the cool-cannoli origin", async () => {
  const response = await handler(
    new Request("https://cool-cannoli-68cac9.netlify.app/.netlify/functions/demo-request", {
      method: "OPTIONS",
      headers: { origin: ORIGIN },
    }),
  );
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("access-control-allow-origin"), ORIGIN);
  assert.match(response.headers.get("access-control-allow-methods"), /POST/);
});

test("rejects non-POST and bad JSON", async () => {
  const get = await handler(new Request("https://example.test/demo-request", { method: "GET" }));
  assert.equal(get.status, 405);
  const bad = await handler(
    new Request("https://example.test/demo-request", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{",
    }),
  );
  assert.equal(bad.status, 400);
  assert.equal((await bad.json()).success, false);
});

test("forwards upstream failure status", async () => {
  const server = listen();
  await once(server, "listening");
  const { port } = server.address();
  process.env.DEMO_REQUEST_UPSTREAM = `http://127.0.0.1:${port}/fail`;
  try {
    const response = await handler(
      new Request("https://example.test/demo-request", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: "ada@example.com", name: "Ada" }),
      }),
    );
    assert.equal(response.status, 500);
    assert.equal((await response.json()).success, false);
  } finally {
    server.close();
  }
});
