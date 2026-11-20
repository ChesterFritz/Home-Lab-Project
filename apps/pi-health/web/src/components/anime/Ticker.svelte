<script>
  import { store } from "../../lib/store.svelte.js";
  import { COPY } from "../../lib/anime.js";
  import { rateStr } from "../../lib/format.js";
  const copy = $derived(COPY[store.anime]);
  const items = $derived.by(() => {
    const s = store.state?.now ?? {}, n = store.state?.alerts?.length ?? 0;
    const live = s.cpu != null ? [`CPU ${s.cpu.toFixed(0)}%`, `${s.temp?.toFixed(0)}°C`, `↓ ${rateStr(s.rx)}`, `${s.watts?.toFixed(1)} W`, n ? `ALERTS ×${n}` : "ALL GREEN"] : [];
    const out = [];
    copy.ticker.forEach((t, i) => { out.push(t); if (live[i]) out.push(live[i]); });
    return out;
  });
</script>

<div class="ticker" aria-hidden="true">
  <div class="track">
    {#each [0, 1] as _}
      <span class="run">{#each items as t}<span class="item">{t}</span><span class="sep">{store.anime === "kuroneko" ? "✦" : "♡"}</span>{/each}</span>
    {/each}
  </div>
</div>

<style>
  .ticker { overflow: hidden; white-space: nowrap; border-bottom: 2.5px solid var(--c-ink); background: var(--c-brand); color: #fff;
    font: 800 13px/1 "M PLUS Rounded 1c", sans-serif; letter-spacing: .04em; position: relative; z-index: 15; }
  :global([data-theme="kuroneko"]) .ticker { background: linear-gradient(90deg, #1b0f2a, #3a1c5c, #1b0f2a); border-color: #a259ff; color: #e6d3ff; font-family: "Yusei Magic", sans-serif; }
  .track { display: inline-flex; animation: scroll 38s linear infinite; padding: 7px 0; }
  .run { display: inline-flex; }
  .item { padding: 0 14px; text-shadow: 1.5px 1.5px 0 rgba(0,0,0,.25); }
  .sep { opacity: .9; }
  @keyframes scroll { to { transform: translateX(-50%); } }
  @media (prefers-reduced-motion: reduce) { .track { animation: none; } }
</style>
