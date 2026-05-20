// Thin API wrapper around fetch().
// The Vite dev server proxies /api → http://localhost:5000 (see vite.config.js).

const BASE = import.meta.env.VITE_API_BASE || "/api";

async function jsonOrThrow(res) {
  const ct = res.headers.get("content-type") || "";
  const body = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const msg =
      (typeof body === "object" && body && (body.message || body.error)) ||
      (typeof body === "string" && body) ||
      `Request failed (${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

export async function analyze(file, lang = "en", mode = "daily") {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("lang", lang);
  fd.append("mode", mode);

  const res = await fetch(`${BASE}/analyze`, { method: "POST", body: fd });
  return jsonOrThrow(res);
}

export async function fetchHistory(limit = 50) {
  const res = await fetch(`${BASE}/history?limit=${limit}`);
  return jsonOrThrow(res);
}

export async function clearHistory() {
  const res = await fetch(`${BASE}/history`, { method: "DELETE" });
  return jsonOrThrow(res);
}

export async function health() {
  const res = await fetch(`${BASE}/health`);
  return jsonOrThrow(res);
}
