// Labels that change in the chuunibyou style. Everything else keeps its plain name.
import { app } from "./store.svelte.js";

const CHUUNI = {
  overview: "Grimoire",
  transactions: "Chronicle",
  accounts: "Vaults",
  settings: "Pact",
  add: "Inscribe record",
  cameIn: "Mana absorbed",
  wentOut: "Mana unleashed",
  leftOver: "Sealed reserve",
  overspent: "Seal broken",
  flow: "Flow of mana",
  trend: "Tides of fortune",
  categories: "Sacrifices",
  networth: "Total dominion",
  latest: "Recent rites",
  netWorthShort: "Dominion",
};

export const word = (key, plain) => (app.anime === "chuuni" ? CHUUNI[key] ?? plain : plain);
