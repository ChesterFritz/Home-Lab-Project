<script>
  // Everything decorative for the anime themes: petals, alert burst, tap sparkles, the secret word.
  import { onMount } from "svelte";
  import { store } from "../../lib/store.svelte.js";
  import { COPY } from "../../lib/anime.js";
  import { sfx } from "../../lib/sfx.js";
  import Petals from "./Petals.svelte";
  import CustomArt from "./CustomArt.svelte";
  const sprite = $derived(store.art("sprite", false));
  const bg = $derived(store.art("bg", false));

  const copy = $derived(COPY[store.anime]);
  let burst = $state(null);        // { text, sub, sev }
  let sparks = $state([]);
  let party = $state(0);           // secret-word party mode (petal boost)
  let seen = null;

  // New alert → big burst.
  $effect(() => {
    const keys = (store.state?.alerts ?? []).map((a) => a.key);
    if (!store.state) return;
    if (seen === null) { seen = new Set(keys); return; }
    const fresh = (store.state.alerts ?? []).find((a) => !seen.has(a.key));
    seen = new Set(keys);
    if (fresh) {
      burst = { text: copy.burst, sub: fresh.title, sev: fresh.severity };
      if (store.sfx) store.anime === "kuroneko" ? sfx.dark() : sfx.alarm();
      setTimeout(() => (burst = null), 2600);
    }
  });

  onMount(() => {
    let id = 0;
    const tap = (e) => {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const glyphs = store.anime === "kuroneko" ? ["✦", "☾", "✧", "†"] : ["♡", "✦", "★", "✧"];
      const n = 7, born = [];
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2 + Math.random() * .5, d = 34 + Math.random() * 26;
        born.push({ id: ++id, x: e.clientX, y: e.clientY, dx: Math.cos(a) * d, dy: Math.sin(a) * d, g: glyphs[i % glyphs.length], hue: i % 3 });
      }
      sparks = [...sparks, ...born];
      setTimeout(() => (sparks = sparks.filter((s) => !born.includes(s))), 750);
    };
    // Type the secret word anywhere for party mode.
    let typed = "";
    const key = (e) => {
      if (e.key.length !== 1) return;
      typed = (typed + e.key.toLowerCase()).slice(-12);
      const word = store.anime === "kuroneko" ? "kuroneko" : "kawaii";
      if (typed.endsWith(word)) {
        party = 1; burst = { text: store.anime === "kuroneko" ? "闇!!" : "かわいい!!", sub: copy.secretSays, sev: "party" };
        if (store.sfx) sfx.sparkle();
        setTimeout(() => (burst = null), 2600); setTimeout(() => (party = 0), 9000);
      }
    };
    addEventListener("pointerdown", tap); addEventListener("keydown", key);
    return () => { removeEventListener("pointerdown", tap); removeEventListener("keydown", key); };
  });
</script>

{#if bg}<div class="char-bg" style="background-image:url('{bg}')" aria-hidden="true"></div>{/if}
<Petals flavor={store.anime} boost={party ? 2.5 : 0} />
{#if sprite}<img class="char-sprite" src={sprite} alt="" aria-hidden="true" draggable="false" />{/if}
<CustomArt />

{#each sparks as s (s.id)}
  <span class="spark h{s.hue}" style="left:{s.x}px;top:{s.y}px;--dx:{s.dx}px;--dy:{s.dy}px" aria-hidden="true">{s.g}</span>
{/each}

{#if burst}
  <div class="burst-wrap" role="alert">
    <div class="burst {burst.sev}">
      <div class="lines"></div>
      <div class="txt">{burst.text}</div>
      <div class="sub">{burst.sub}</div>
    </div>
  </div>
{/if}

<style>
  .char-bg { position: fixed; inset: 0; z-index: 0; background-size: cover; background-position: center; pointer-events: none; }
  .char-bg::after { content: ""; position: absolute; inset: 0; background: rgba(255, 228, 240, .72); }
  :global([data-theme="kuroneko"]) .char-bg::after { background: rgba(13, 8, 20, .74); }
  .char-sprite { position: fixed; z-index: 6; right: max(8px, calc((100vw - 1240px) / 2 - 260px)); bottom: calc(64px + env(safe-area-inset-bottom));
    height: min(46vh, 520px); max-width: 42vw; object-fit: contain; object-position: bottom; pointer-events: none;
    filter: drop-shadow(0 6px 18px rgba(0,0,0,.25)); animation: sway 5s ease-in-out infinite; transform-origin: 50% 100%; }
  /* Behind the content it's a faint watermark so text stays readable; with room to spare beside the page, full strength. */
  .char-sprite { opacity: .3; }
  @media (min-width: 1024px) { .char-sprite { bottom: 0; } }
  @media (min-width: 1760px) { .char-sprite { opacity: 1; } }
  @media (max-width: 1023px) { .char-sprite { height: 34vh; } }
  @keyframes sway { 0%, 100% { transform: rotate(-1deg); } 50% { transform: rotate(1deg) translateY(-4px); } }
  @media (prefers-reduced-motion: reduce) { .char-sprite { animation: none; } }
  .spark { position: fixed; z-index: 60; pointer-events: none; font-size: 18px; font-weight: 900; transform: translate(-50%, -50%);
    animation: fly .75s ease-out forwards; text-shadow: 0 0 6px #fff; }
  .spark.h0 { color: #ff4fa3; } .spark.h1 { color: #ff9a3c; } .spark.h2 { color: #ffd23f; }
  :global([data-theme="kuroneko"]) .spark.h0 { color: #b07cff; } :global([data-theme="kuroneko"]) .spark.h1 { color: #e11d48; } :global([data-theme="kuroneko"]) .spark.h2 { color: #f1e9ff; }
  @keyframes fly { to { transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) scale(.3) rotate(160deg); opacity: 0; } }

  .burst-wrap { position: fixed; inset: 0; z-index: 70; display: grid; place-items: center; pointer-events: none; }
  .burst { position: relative; padding: 46px 56px; text-align: center; animation: pop 2.6s cubic-bezier(.2,1.6,.4,1) forwards;
    clip-path: polygon(50% 0, 60% 14%, 78% 4%, 80% 22%, 100% 20%, 90% 38%, 100% 52%, 88% 62%, 98% 80%, 78% 78%, 72% 98%, 58% 84%, 46% 100%, 38% 82%, 18% 94%, 20% 74%, 0 72%, 12% 56%, 2% 38%, 20% 34%, 14% 12%, 36% 18%);
    background: #ffe94d; filter: drop-shadow(0 0 0 #000); }
  .burst.critical, .burst.serious { background: #ff3b6b; } .burst.party { background: #ff8fc6; }
  :global([data-theme="kuroneko"]) .burst { background: #2a0f45; } :global([data-theme="kuroneko"]) .burst.critical { background: #5c0b23; }
  .lines { position: absolute; inset: 0; background: repeating-conic-gradient(from 0deg, rgba(255,255,255,.35) 0 4deg, transparent 4deg 12deg); }
  .txt { position: relative; font: 400 clamp(54px, 15vw, 120px)/1 "Dela Gothic One", sans-serif; color: #fff;
    -webkit-text-stroke: 3px #3a1030; paint-order: stroke fill; text-shadow: 6px 6px 0 #3a1030; transform: rotate(-6deg); }
  :global([data-theme="kuroneko"]) .txt { -webkit-text-stroke-color: #000; text-shadow: 0 0 18px #a259ff, 5px 5px 0 #000; color: #f1e9ff; }
  .sub { position: relative; margin-top: 10px; font: 800 16px "M PLUS Rounded 1c", sans-serif; color: #3a1030; max-width: 18em; }
  :global([data-theme="kuroneko"]) .sub { color: #e6d3ff; font-family: "Yusei Magic", sans-serif; }
  @keyframes pop { 0% { transform: scale(0) rotate(-20deg); opacity: 0; } 12% { transform: scale(1.12) rotate(3deg); opacity: 1; }
    20% { transform: scale(1) rotate(0); } 85% { transform: scale(1); opacity: 1; } 100% { transform: scale(1.3); opacity: 0; } }
  @media (prefers-reduced-motion: reduce) { .burst { animation: none; } }
</style>
