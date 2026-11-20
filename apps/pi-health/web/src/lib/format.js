export function rate(bps) {
  const b = (bps || 0) * 8;
  if (b >= 1e6) return [(b / 1e6).toFixed(b >= 1e8 ? 0 : 1), "Mb/s"];
  if (b >= 1e3) return [(b / 1e3).toFixed(b >= 1e5 ? 0 : 1), "kb/s"];
  return [b.toFixed(0), "b/s"];
}
export const rateStr = (b) => rate(b).join(" ");

export function bytes(n) {
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < 4) { n /= 1024; i++; }
  return (n >= 100 || !i ? n.toFixed(0) : n.toFixed(1)) + " " + u[i];
}

export function dur(sec, long = false) {
  sec = Math.max(0, Math.floor(sec || 0));
  const d = Math.floor(sec / 86400), h = Math.floor((sec % 86400) / 3600), m = Math.floor((sec % 3600) / 60);
  if (long) {
    const p = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
    if (d) return `${p(d, "day")}, ${p(h, "hour")}`;
    if (h) return `${p(h, "hour")}, ${p(m, "minute")}`;
    return m ? p(m, "minute") : p(sec, "second");
  }
  if (d) return `${d}d ${h}h`;
  if (h) return `${h}h ${m}m`;
  if (m) return `${m} min`;
  return `${sec} s`;
}

export const ago = (t, now) => (now - t < 45 ? "just now" : dur(now - t) + " ago");
export const fullTime = (t) => new Date(t * 1000).toLocaleString();
