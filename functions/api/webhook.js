// File: functions/api/webhook.js
export async function onRequest(context) {
  const url = new URL(context.request.url);

  // === Verification (GET)
  if (context.request.method === "GET") {
    const VERIFY_TOKEN = "equallemeta"; // придумай свой токен
    const token = url.searchParams.get("hub.verify_token");
    const challenge = url.searchParams.get("hub.challenge");

    if (token === VERIFY_TOKEN) {
      return new Response(challenge, { status: 200 });
    }
    return new Response("Verification failed", { status: 403 });
  }

  // === Incoming Webhook (POST)
  if (context.request.method === "POST") {
    const body = await context.request.json();
    console.log("📩 Meta Webhook Event:", JSON.stringify(body));
    return new Response("OK", { status: 200 });
  }

  return new Response("Unsupported method", { status: 405 });
}
