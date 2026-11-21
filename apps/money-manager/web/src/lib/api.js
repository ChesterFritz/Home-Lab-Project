// Thin client for server.py's /api/* and /auth/*. Errors carry the server's plain-language message.
export class SignedOut extends Error {}

async function call(method, path, body, base = "/api/") {
  const res = await fetch(base + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON error page */
  }
  if (res.status === 401 && path !== "login") throw new SignedOut(data?.error || "Sign in to continue.");
  if (!res.ok) throw new Error(data?.error || `The server answered ${res.status}. Is Money Manager running?`);
  return data;
}

const qs = (o) => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== undefined && v !== "")).toString();

export const api = {
  meta: () => call("GET", "meta"),
  transactions: (from, to, account) => call("GET", "transactions?" + qs({ from, to, account })),
  summary: (from, to) => call("GET", "summary?" + qs({ from, to })),
  trend: (end, months = 12) => call("GET", "trend?" + qs({ end, months })),
  networth: (months = 12) => call("GET", "networth?" + qs({ months })),
  accountHistory: (id, weeks = 26) => call("GET", "account-history?" + qs({ id, weeks })),
  saveTransaction: (body) => call("POST", "transactions", body),
  deleteTransaction: (id) => call("DELETE", "transactions/" + encodeURIComponent(id)),
  saveAccount: (body) => call("POST", "accounts", body),
  deleteAccount: (id) => call("DELETE", "accounts/" + encodeURIComponent(id)),
};

const auth = (method, path, body) => call(method, path, body, "/auth/");
export const session = {
  me: () => auth("GET", "me"),
  login: (username, password) => auth("POST", "login", { username, password }),
  register: (username, password) => auth("POST", "register", { username, password }),
  logout: () => auth("POST", "logout", {}),
  changePassword: (current, next) => auth("POST", "password", { current, new: next }),
  setAvatar: (image) => auth("POST", "avatar", { image }),
};
