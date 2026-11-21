import { api, session, SignedOut } from "./api.js";
import { setSymbol, ym } from "./fmt.js";

const VIEWS = ["overview", "transactions", "accounts", "settings"];

function viewFromHash() {
  const v = location.hash.replace(/^#\/?/, "").split("?")[0];
  return VIEWS.includes(v) ? v : "overview";
}

/** #/overview?m=2026-08 opens a specific month. */
function monthFromHash() {
  const m = new URLSearchParams(location.hash.split("?")[1] || "").get("m");
  return /^\d{4}-\d{2}$/.test(m || "") ? m : ym(new Date());
}

/** Everything views share: reference data, the selected month, the edit sheet and toasts. */
export const app = $state({
  view: viewFromHash(),
  month: monthFromHash(),
  meta: null,
  error: "",
  /** "glass" or "anime" (the hidden style: tap the logo 7 times). */
  skin: (() => {
    try {
      return localStorage.getItem("pitaka-skin") === "anime" ? "anime" : "glass";
    } catch {
      return "glass";
    }
  })(),
  /** The anime style as resolved for light/dark: "manga" | "chuuni" | null. */
  anime: null,
  dark: false,
  animeUnlocked: (() => {
    try {
      return localStorage.getItem("pitaka-anime-unlocked") === "1";
    } catch {
      return false;
    }
  })(),
  /** undefined while checking, null when signed out, { username } when signed in. */
  user: undefined,
  /** Bumped after every save/delete so views refetch. */
  version: 0,
  /** { mode: "tx", tx?, kind? } | { mode: "account", account? } | null */
  sheet: null,
  toast: null,
  /** Category filter handed from Overview to Transactions. */
  categoryFilter: null,
});

addEventListener("hashchange", () => (app.view = viewFromHash()));

// #/overview?add=expense opens the add sheet straight away (handy as a home-screen shortcut).
{
  const add = new URLSearchParams(location.hash.split("?")[1] || "").get("add");
  if (["expense", "income", "transfer"].includes(add)) app.sheet = { mode: "tx", kind: add };
}

export function go(view, extra = {}) {
  Object.assign(app, extra);
  location.hash = "/" + view;
  app.view = view;
  scrollTo({ top: 0, behavior: "instant" });
}

export async function loadMeta() {
  try {
    app.meta = await api.meta();
    setSymbol(app.meta.currency.symbol);
    app.error = "";
  } catch (e) {
    if (e instanceof SignedOut) return signedOut();
    app.error = e.message;
  }
}

function signedOut() {
  app.user = null;
  app.meta = null;
  app.sheet = null;
}

/** On load: who is signed in? Then fetch their book. */
export async function boot() {
  try {
    app.user = await session.me();
    await loadMeta();
  } catch (e) {
    if (e instanceof SignedOut) signedOut();
    else (app.user = null), (app.error = e.message);
  }
}

export async function signIn(mode, username, password) {
  app.user = await (mode === "register" ? session.register(username, password) : session.login(username, password));
  app.error = "";
  app.version++;
  await loadMeta();
}

export async function signOut() {
  await session.logout().catch(() => {});
  signedOut();
  location.hash = "/overview";
}

/** Call after any write: refresh balances and tell open views to refetch. */
export async function changed(message) {
  await loadMeta();
  app.version++;
  if (message) toast(message);
}

let toastTimer;
export function toast(text, tone = "ok") {
  clearTimeout(toastTimer);
  app.toast = { text, tone, id: Date.now() };
  toastTimer = setTimeout(() => (app.toast = null), 3200);
}

export const accountName = (id) => app.meta?.accounts.find((a) => a.id === id)?.name ?? "";

export function openAdd(kind = "expense") {
  // Entries need an account to live in; with none yet, start there instead.
  app.sheet = app.meta && !app.meta.accounts.length ? { mode: "account", account: null } : { mode: "tx", kind };
}
export function openEdit(tx) {
  app.sheet = { mode: "tx", tx };
}
export function openAccount(account = null) {
  app.sheet = { mode: "account", account };
}

// ---------------------------------------------------------------- the secret anime style
// Skin "anime" resolves by light/dark: light = black-and-white manga, dark = chuunibyou.
// <html data-anime="manga|chuuni"> drives the CSS; index.html sets it early to avoid a flash.
const root = document.documentElement;
const darkQuery = matchMedia("(prefers-color-scheme: dark)");
const readDark = () => (root.dataset.theme ? root.dataset.theme === "dark" : darkQuery.matches);

export function syncAnime() {
  app.dark = readDark();
  const mode = app.skin === "anime" ? (app.dark ? "chuuni" : "manga") : null;
  if (mode) root.dataset.anime = mode;
  else delete root.dataset.anime;
  app.anime = mode;
}
darkQuery.addEventListener("change", syncAnime);
new MutationObserver(syncAnime).observe(root, { attributes: true, attributeFilter: ["data-theme"] });

export function setSkin(skin) {
  app.skin = skin;
  try {
    skin === "anime" ? localStorage.setItem("pitaka-skin", "anime") : localStorage.removeItem("pitaka-skin");
    if (skin === "anime") localStorage.setItem("pitaka-anime-unlocked", "1");
  } catch {
    /* private mode: the style just won't be remembered */
  }
  if (skin === "anime") app.animeUnlocked = true;
  syncAnime();
}
syncAnime();
