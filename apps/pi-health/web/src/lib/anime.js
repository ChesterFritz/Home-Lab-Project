// Text for the character themes (Kirino, Kuroneko, Viking). {placeholders} are filled from live readings.
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
  viking: {
    brand: "ᛟᚱᚨᚾᚷᛖ ᛈᛁ · ᛞᚱᚨᚲᛟᚾ ᚺᚨᛚᛚ",
    brandEn: "Hall of the Iron Dragon",
    good: ["The longhouse stands. All is well!", "The fjord is calm and the dragons sleep.", "The ravens report: all systems normal.", "Shields up, mead out. Nothing to fight today!"],
    goodSub: "{checks} watchmen reported in. The last patrol rode out {ago}.",
    alert: "To arms! {title}!",
    alertSub: "{detail}. Raiders were sighted {since} ago. Sound the horn!",
    offline: "The bridge to the island has fallen!",
    offlineSub: "Fog hides the Pi from view. Check its power, or sail back to the home network. The horn will sound when it returns.",
    connecting: "Lighting the signal fires…",
    quips: [
      "Rawr! My dragonfire runs at {temp}°C.",
      "The forge burns at {cpu}% today. Pump the bellows!",
      "{mem}% of the treasure hoard is full. Need a bigger cave.",
      "The ravens carried your DNS answer in {dns} ms.",
      "{uptime} without a nap. Even dragons need sleep, you know.",
      "I'm not a lizard. I'm a FEARSOME beast. …Scratch behind my horns?",
      "No ads shall pass the shieldwall!",
      "Skål! To another day of uptime!",
      "I tried riding a dragon once. Then I remembered I AM the dragon.",
      "The Uptime Kuma lookout never sleeps. Neither do I. Mostly.",
    ],
    worried: ["Smoke on the horizon…", "The sea grows restless…"],
    heads: { apps: ["Apps", "ᚨᚱᛗᛟᚱᚤ · Armory"], history: ["History", "ᛋᚨᚷᚨ · Saga"], services: ["Services", "ᛋᚺᛁᛖᛚᛞᚹᚨᛚᛚ"], alerts: ["Alert history", "ᚺᛟᚱᚾ · War horn"] },
    burst: "TO ARMS!!",
    ticker: ["ᛟᚱᚨᚾᚷᛖ ᛈᛁ", "Dragon riders on watch", "ᚠᛁᛟᚱᛞ ᛁᛋ ᚲᚨᛚᛗ", "The fjord is calm", "SKÅL!"],
    tabs: { overview: "Longhouse", charts: "Sagas", services: "Shieldwall", alerts: "War horn" },
    secretSays: "The mead hall roars! A feast for the dragon riders!",
  },
};

// Per-theme bits used across components.
export const GLYPH = { kirino: "♡", kuroneko: "✦", viking: "⚔" };
export const NAME = { kirino: "Kirino", kuroneko: "Kuroneko", viking: "Viking" };
export const MASCOT = { kirino: "Pi-chan", kuroneko: "the familiar", viking: "the dragon" };
export const SECRET = { kirino: "kawaii", kuroneko: "kuroneko", viking: "valhalla" };
export const SECRET_BURST = { kirino: "かわいい!!", kuroneko: "闇!!", viking: "SKÅL!!" };
export const SPARKS = { kirino: ["♡", "✦", "★", "✧"], kuroneko: ["✦", "☾", "✧", "†"], viking: ["ᚠ", "ᚱ", "ᛟ", "✦", "ᛉ"] };

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
const VIKING_SFX = { cpu: "CLANG!", temp: "FWOOSH!", gpu: "WHIRR!", power: "THOOM!", net: "WHOOSH!", mem: "HEAVE!" };
export function sfxFor(kind, s, flavor) {
  if (!s) return null;
  if (flavor === "viking") return sfxFor(kind, s) && VIKING_SFX[kind];
  if (kind === "cpu" && s.cpu >= 60) return "ドドド";
  if (kind === "temp" && s.temp >= 65) return "ゴゴゴ";
  if (kind === "gpu" && s.gpu >= 50) return "ギュイン";
  if (kind === "power" && s.watts >= 2.5) return "バチッ";
  if (kind === "net" && (s.rx + s.tx) >= 1.25e5) return "ビュン!";
  if (kind === "mem" && s.mem >= 75) return "ギュウ";
  return null;
}

const ANIME_KAO = { cpu: "(￣▽￣)ノ", temp: "(〃▽〃)", gpu: "( ˘ω˘ )", power: "ϟ(｀ω´)", net: "┌(>_<)┘", mem: "(｡•̀ᴗ-)✧" };
export const KAOMOJI = {
  kirino: ANIME_KAO, kuroneko: ANIME_KAO,
  viking: { cpu: "ᚦ forge", temp: "ᚲ hearth", gpu: "ᛃ gears", power: "ᛏ thunder", net: "ᚱ ravens", mem: "ᚠ hoard" },
};
