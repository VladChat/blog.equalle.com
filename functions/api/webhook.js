// File: functions/api/webhook.js
export async function onRequest(context) {
  const url = new URL(context.request.url);

  // === Verification (GET)
  if (context.request.method === "GET") {
    const VERIFY_TOKEN = "equallemeta"; // придумай свой токен (тот же, что укажешь в Meta)
    const token = url.searchParams.get("hub.verify_token");
    const challenge = url.searchParams.get("hub.challenge");

    if (token === VERIFY_TOKEN) {
      return new Response(challenge, { status: 200 });
    }

    return new Response("Verification failed", { status: 403 });
  }

  // === Incoming Webhook (POST)
  if (context.request.method === "POST") {
    try {
      const body = await context.request.json();
      console.log("📩 Meta Webhook Event:", JSON.stringify(body, null, 2));
      return new Response("OK", { status: 200 });
    } catch (err) {
      console.error("❌ Error parsing webhook body:", err);
      return new Response("Bad Request", { status: 400 });
    }
  }

  // === Unsupported methods
  return new Response("Unsupported method", { status: 405 });
}
