// Proxies the live waitlist form to the Render agent.
// The SPA posts to /.netlify/functions/demo-request and only treats HTTP ok as success.
const DEFAULT_UPSTREAM = "https://tobinai.onrender.com/webhook/demo-request";
const ALLOWED_ORIGINS = new Set(["https://cool-cannoli-68cac9.netlify.app"]);

function upstreamUrl() {
  const configured = (process.env.DEMO_REQUEST_UPSTREAM || "").trim();
  return configured || DEFAULT_UPSTREAM;
}

function corsHeaders(request) {
  const origin = request.headers.get("origin");
  const allow = origin && ALLOWED_ORIGINS.has(origin) ? origin : "*";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
  };
}

function json(status, body, request) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(request),
    },
  });
}

export default async (request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(request) });
  }

  if (request.method !== "POST") {
    return json(405, { success: false, error: "Method not allowed" }, request);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { success: false, error: "JSON body is required" }, request);
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return json(400, { success: false, error: "JSON object is required" }, request);
  }

  try {
    const upstream = await fetch(upstreamUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(55_000),
    });
    const text = await upstream.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      payload = {
        success: false,
        error: "Upstream returned a non-JSON response",
      };
    }
    return json(upstream.status || 502, payload, request);
  } catch (error) {
    console.error("demo-request proxy error:", error);
    return json(
      502,
      { success: false, error: "Demo request upstream unavailable" },
      request,
    );
  }
};
