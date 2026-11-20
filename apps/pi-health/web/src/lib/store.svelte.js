// Polls the Pi every 2 s and keeps history buffers. Shared by every component.
export const RANGES = { "5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "24h": 86400 };
const KEYS = ["t", "cpu", "temp", "gpu", "gpu_mhz", "cpu_mhz", "rx", "tx", "vrx", "vtx", "mem", "swap", "watts"];

function load(key, fallback) { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } }
function save(key, v) { try { localStorage.setItem(key, v); } catch {} }

class Store {
  state = $state.raw(null);        // /api/state
  hist = $state.raw(null);         // history for the selected range
  live = $state.raw(null);         // last 5 minutes, for sparklines
  range = $state(RANGES[load("pihealth-range")] ? load("pihealth-range") : "15m");
  tab = $state("overview");        // mobile tabs
  status = $state("connecting");   // connecting | live | offline
  lastOk = $state(0);
  now = $state(Date.now() / 1000); // Pi clock, ticks with each poll
  theme = $state(load("pihealth-theme", ""));   // "" (system) | light | dark | kirino | kuroneko
  sfx = $state(load("pihealth-sfx", "") === "on");
  custom = $state.raw({});         // uploaded character pictures: { "kirino-main": "custom/…" }
  artOpen = $state(false);
  #fails = 0;
  #timer = null;

  setRange(r) { this.range = r; save("pihealth-range", r); this.hist = null; this.loadHistory(); }
  setTab(t) { this.tab = t; window.scrollTo({ top: 0 }); }
  get anime() { return this.theme === "kirino" || this.theme === "kuroneko" ? this.theme : null; }
  setTheme(t) {
    this.theme = t;
    if (t) document.documentElement.dataset.theme = t;
    else delete document.documentElement.dataset.theme;
    save("pihealth-theme", t);
    const color = { kirino: "#ffe4f0", kuroneko: "#120d1a", dark: "#0e1114", light: "#eef1f4" }[t];
    document.querySelectorAll('meta[name="theme-color"]').forEach((m) => {
      if (!m.dataset.orig) m.dataset.orig = m.content;
      m.content = color ?? m.dataset.orig;
    });
  }
  async loadCustom() {
    try { this.custom = await fetch("api/custom", { cache: "no-store" }).then((r) => r.json()); } catch {}
  }
  async uploadCustom(slot, file) {
    const r = await fetch(`api/custom/${slot}`, { method: "PUT", body: file });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.error || `Upload failed (${r.status})`);
    this.custom = body;
  }
  async removeCustom(slot) {
    const r = await fetch(`api/custom/${slot}`, { method: "DELETE" });
    if (r.ok) this.custom = await r.json();
  }
  // Picture for a slot kind, falling back to the flavor's main picture.
  art(kind, fallback = true) {
    const f = this.anime; if (!f) return null;
    return this.custom[`${f}-${kind}`] ?? (fallback ? this.custom[`${f}-main`] : null) ?? null;
  }
  setSfx(on) { this.sfx = on; save("pihealth-sfx", on ? "on" : ""); }

  async loadHistory() {
    try {
      const get = (r) => fetch(`api/history?range=${r}`, { cache: "no-store" }).then((x) => x.json());
      const [h, l] = await Promise.all([get(this.range), this.range === "5m" ? null : get("5m")]);
      this.hist = h;
      this.live = l || h;
    } catch {}
  }

  #append(buf, s, keep) {
    if (!buf || !s || (buf.t.length && s.t <= buf.t[buf.t.length - 1])) return buf;
    let start = 0;
    while (start < buf.t.length && buf.t[start] < s.t - keep) start++;
    const out = {};
    for (const k of KEYS) out[k] = [...buf[k].slice(start), s[k] ?? null];
    return out;
  }

  async poll() {
    try {
      const r = await fetch("api/state", { cache: "no-store" });
      if (!r.ok) throw new Error(String(r.status));
      const st = await r.json();
      this.state = st;
      this.now = st.server_time;
      this.lastOk = Date.now();
      this.#fails = 0;
      this.status = "live";
      if (RANGES[this.range] <= 3600) this.hist = this.#append(this.hist, st.now, RANGES[this.range]);
      this.live = this.#append(this.live, st.now, 300);
    } catch {
      if (++this.#fails >= 2) this.status = "offline";
    }
  }

  start() {
    // ?theme=kirino (or kuroneko, light, dark) in the address picks a theme, handy for sharing.
    const q = new URLSearchParams(location.search).get("theme");
    if (q !== null && ["", "light", "dark", "kirino", "kuroneko"].includes(q)) this.setTheme(q);
    else if (this.theme) this.setTheme(this.theme);
    const go = () => { clearInterval(this.#timer); this.poll(); this.#timer = setInterval(() => this.poll(), 2000); };
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) clearInterval(this.#timer);
      else { this.loadHistory(); go(); }
    });
    setInterval(() => { if (!document.hidden && RANGES[this.range] > 3600) this.loadHistory(); }, 60000);
    this.loadHistory();
    this.loadCustom();
    go();
  }
}

export const store = new Store();
