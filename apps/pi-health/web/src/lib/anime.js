// Text for the two anime themes. {placeholders} are filled from live readings.
import { dur } from "./format.js";

export const COPY = {
  kirino: {
    brand: "俺のPiがこんなに可愛いわけがない",
    brandEn: "My Pi can't be this cute!",
    good: ["Everything's fine… not that I care!", "Hmph. All systems normal. Obviously.", "It's running perfectly. Because I'm perfect."],
    goodSub: "{checks} checks passed. D-don't get the wrong idea, I only checked {ago}!",
    alert: "B-baka! {title}!",
    alertSub: "{detail}. It started {since} ago and you didn't even notice?!",
    offline: "Where did you go?! I can't reach the Pi!",
    offlineSub: "Is it unplugged? Are you on the wrong network? Ugh, fix it! I'll keep trying… not because I want to.",
    connecting: "Hold on, I'm getting ready!",
    quips: [
      "Stop poking me, idiot!",
      "CPU at {cpu}%… I'm totally not working hard.",
      "It's {temp}°C in here… it's NOT because I'm blushing!",
      "I blocked ads all day. You're welcome. …Not that I did it for you!",
      "Up for {uptime}. Impressive, right? Praise me!",
      "Don't touch my settings without asking!",
      "{mem}% of memory used. A girl needs space, you know.",
      "DNS answered in {dns} ms. Faster than you, slowpoke.",
      "It's not like I wanted to show you these charts…",
      "You keep checking on me… w-weirdo.",
    ],
    worried: ["Ugh, something's off… do something!", "H-hey, this isn't my fault!"],
    heads: { apps: ["Apps", "アプリ ♡"], history: ["History", "履歴 ☆"], services: ["Services", "サービス ✦"], alerts: ["Alert history", "アラート ♡"] },
    burst: "KYAA!!",
    ticker: ["俺のPiがこんなに可愛いわけがない", "My Pi can't be this cute!", "ツンデレ監視中", "Tsundere mode: ON", "かわいい ♡"],
    tabs: { overview: "Home ♡", charts: "Charts", services: "Services", alerts: "Alerts" },
    secretSays: "W-what?! Who taught you that word?!",
  },
  kuroneko: {
    brand: "俺のPiがこんなに可愛いわけがない",
    brandEn: "The Pi of the fallen angel",
    good: ["The seal holds. All daemons obey.", "Darkness is in balance. All is well.", "My familiars report no disturbance."],
    goodSub: "{checks} wards inspected. The last ritual was performed {ago}.",
    alert: "A curse stirs: {title}",
    alertSub: "{detail}. The omen appeared {since} ago.",
    offline: "The link to the Pi realm has been severed…",
    offlineSub: "Restore the power crystal or return to the home network. I shall wait in the dark.",
    connecting: "Summoning the Pi…",
    quips: [
      "Kneel, mortal. The core burns at {temp}°C.",
      "{cpu}% of my dark power is in use.",
      "I have bound {mem}% of memory to my will.",
      "The DNS familiar answers in {dns} ms.",
      "Fufu… {uptime} without rest. Such is the stamina of a fallen angel.",
      "Don't touch me, you're not worthy… f-fine. Once.",
      "The Uptime Kuma oracle watches. Always.",
      "Within this silicon sleeps a power you cannot fathom.",
    ],
    worried: ["The omens are dire…", "A disturbance in the daemon realm…"],
    heads: { apps: ["Apps", "眷属"], history: ["History", "黙示録"], services: ["Services", "結界"], alerts: ["Alert history", "呪いの記録"] },
    burst: "呪!!",
    ticker: ["堕天聖黒猫", "The night is mine", "闇の結界 稼働中", "Fallen angel mode", "我が名は黒猫"],
    tabs: { overview: "Sanctum", charts: "Omens", services: "Wards", alerts: "Curses" },
    secretSays: "You know the forbidden word… Interesting.",
  },
};

export function fill(text, vars) {
  return text.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? "?"));
}

export function vars(state, now) {
  const s = state?.now ?? {}, c = state?.checks ?? {};
  return {
    cpu: s.cpu?.toFixed(0), temp: s.temp?.toFixed(0), mem: s.mem?.toFixed(0),
    dns: c.dns?.ms != null ? Math.round(c.dns.ms) : "?", uptime: c.uptime ? dur(c.uptime, true) : "a while",
  };
}

// Big sound-effect words that appear on readouts when values climb.
export function sfxFor(kind, s) {
  if (!s) return null;
  if (kind === "cpu" && s.cpu >= 60) return "ドドド";
  if (kind === "temp" && s.temp >= 65) return "ゴゴゴ";
  if (kind === "gpu" && s.gpu >= 50) return "ギュイン";
  if (kind === "power" && s.watts >= 2.5) return "バチッ";
  if (kind === "net" && (s.rx + s.tx) >= 1.25e5) return "ビュン!";
  if (kind === "mem" && s.mem >= 75) return "ギュウ";
  return null;
}

export const KAOMOJI = {
  cpu: "(￣▽￣)ノ", temp: "(〃▽〃)", gpu: "( ˘ω˘ )", power: "ϟ(｀ω´)", net: "┌(>_<)┘", mem: "(｡•̀ᴗ-)✧",
};
