// File: functions/api/webhook.js
export async function onRequest({ request, env }) {
  const url = new URL(request.url);

  // === GET: verification
  if (request.method === "GET") {
    const token = url.searchParams.get("hub.verify_token");
    const challenge = url.searchParams.get("hub.challenge");
    if (token && env.VERIFY_TOKEN && token === env.VERIFY_TOKEN) {
      return new Response(challenge, { status: 200 });
    }
    return new Response("Verification failed", { status: 403 });
  }

  // === POST: signature validation (X-Hub-Signature-256)
  if (request.method === "POST") {
    const signature = request.headers.get("x-hub-signature-256") || "";
    const raw = await request.text();

    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey(
      "raw",
      enc.encode(env.APP_SECRET),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const mac = await crypto.subtle.sign("HMAC", key, enc.encode(raw));
    const hex = [...new Uint8Array(mac)].map(b => b.toString(16).padStart(2, "0")).join("");
    const expected = `sha256=${hex}`;

    if (signature !== expected) {
      return new Response("Invalid signature", { status: 403 });
    }

    // ok
    const body = JSON.parse(raw);
    console.log("📩 Meta Webhook Event:", JSON.stringify(body));
    return new Response("OK", { status: 200 });
  }

  return new Response("Method Not Allowed", { status: 405 });
}
