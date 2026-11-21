const nf = new Intl.NumberFormat("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf0 = new Intl.NumberFormat("en-PH", { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("en-PH", { notation: "compact", maximumFractionDigits: 1 });

export let symbol = "₱";
export const setSymbol = (s) => (symbol = s || "₱");

/** ₱1,234.50 — negative values get a true minus sign, not a hyphen. */
export function peso(v, { sign = false, whole = false } = {}) {
  const n = Number(v) || 0;
  const body = (whole ? nf0 : nf).format(Math.abs(n));
  const s = n < 0 ? "−" : sign && n > 0 ? "+" : "";
  return `${s}${symbol}${body}`;
}
export const pesoShort = (v) => `${v < 0 ? "−" : ""}${symbol}${compact.format(Math.abs(v))}`;

export const pad = (n) => String(n).padStart(2, "0");
export const ym = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
export const iso = (d) => `${ym(d)}-${pad(d.getDate())}`;

export function monthRange(key) {
  const [y, m] = key.split("-").map(Number);
  const last = new Date(y, m, 0).getDate();
  return { from: `${key}-01`, to: `${key}-${pad(last)}` };
}
export function shiftMonth(key, k) {
  const [y, m] = key.split("-").map(Number);
  return ym(new Date(y, m - 1 + k, 1));
}
export const monthName = (key, opts = { month: "long", year: "numeric" }) => {
  const [y, m] = key.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-PH", opts);
};
export const monthShort = (key) => monthName(key, { month: "short" });

export function dayLabel(isoDay, today) {
  if (isoDay === today) return "Today";
  const t = new Date(today + "T00:00:00");
  t.setDate(t.getDate() - 1);
  if (isoDay === iso(t)) return "Yesterday";
  const d = new Date(isoDay + "T00:00:00");
  return d.toLocaleDateString("en-PH", { weekday: "long", month: "short", day: "numeric" });
}

/** Split a leading emoji off a category name ("🍜 Food" → ["🍜", "Food"]). */
export function splitEmoji(name = "") {
  const m = name.match(/^(\p{Extended_Pictographic}(?:\p{Emoji_Modifier}|️|‍\p{Extended_Pictographic})*)\s*(.*)$/u);
  return m ? [m[1], m[2]] : ["", name];
}
