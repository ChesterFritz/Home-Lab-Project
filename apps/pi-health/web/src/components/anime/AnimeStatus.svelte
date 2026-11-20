<script>
  import { store } from "../../lib/store.svelte.js";
  import { COPY, fill, vars } from "../../lib/anime.js";
  import { dur, ago } from "../../lib/format.js";
  import { sfx } from "../../lib/sfx.js";
  import Mascot from "./Mascot.svelte";
  import SevIcon from "../SevIcon.svelte";

  const copy = $derived(COPY[store.anime]);
  const st = $derived(store.state);
  const c = $derived(st?.checks ?? {});
  const alerts = $derived(st?.alerts ?? []);
  const offline = $derived(store.status === "offline");
  const sev = $derived(offline ? "offline" : alerts[0]?.severity ?? "good");
  const mood = $derived(offline ? "dizzy" : sev === "critical" || sev === "serious" ? "angry" : sev === "warning" ? "worried" : quip >= 0 ? "happy" : "normal");
  const checks = $derived((c.containers?.length ?? 0) + (c.links ?? []).filter((l) => l.up != null).length + 5);
  let quip = $state(-1);
  let pick = $state(Math.floor(Math.random() * 3));
  let timer;

  const headline = $derived(
    offline ? copy.offline : !st ? copy.connecting
    : alerts.length ? fill(copy.alert, { title: alerts[0].title })
    : copy.good[pick % copy.good.length]);
  const sub = $derived(
    offline ? copy.offlineSub : !st ? ""
    : alerts.length ? fill(copy.alertSub, { detail: alerts[0].detail || "Something's wrong", since: dur(store.now - alerts[0].since, true) })
    : fill(copy.goodSub, { checks, ago: c.t ? ago(c.t, store.now) : "just now" }));
  const bubble = $derived.by(() => {
    if (quip < 0) return alerts.length ? copy.worried[0] : null;
    return fill(copy.quips[quip % copy.quips.length], vars(st, store.now));
  });

  const pic = $derived(store.art(mood));
  let squish = $state(false);
  function poke() {
    squish = false; requestAnimationFrame(() => (squish = true));
    quip = (quip + 1 + Math.floor(Math.random() * 3)) % copy.quips.length;
    pick++;
    if (store.sfx) sfx.boop();
    clearTimeout(timer); timer = setTimeout(() => (quip = -1), 7000);
  }
</script>

<section class="anime-status card relative overflow-hidden" data-sev={sev} aria-live="polite">
  <div class="speed" aria-hidden="true"></div>
  <div class="relative flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:gap-6 sm:p-6">
    <div class="flex items-end gap-3 sm:block">
      {#if pic}
        <button type="button" class="char-pic {squish ? 'squish' : ''}" onclick={poke} onanimationend={() => (squish = false)}
          aria-label="Your character picture. Tap to hear what she thinks.">
          <img src={pic} alt="" draggable="false" />
        </button>
      {:else}
        <Mascot {mood} flavor={store.anime} size={112} onpoke={poke} />
      {/if}
      {#if bubble}
        <div class="bubble sm:hidden">{bubble}</div>
      {/if}
    </div>
    <div class="min-w-0 flex-1">
      {#if bubble}<div class="bubble mb-3 hidden sm:inline-block">{bubble}</div>{/if}
      <h1 class="headline">{headline}</h1>
      {#if sub}<p class="sub">{sub}</p>{/if}

      {#if alerts.length > 1 && !offline}
        <ul class="mt-3 space-y-1.5">
          {#each alerts.slice(1) as a (a.key)}
            <li class="flex items-center gap-2 text-[14px] font-bold"><SevIcon sev={a.severity} size={16} /><span class="min-w-0 flex-1 truncate">{a.title}</span></li>
          {/each}
        </ul>
      {/if}

      {#if c.uptime}
        <div class="mt-4 flex flex-wrap gap-2">
          <span class="chip">Up for <b>{dur(c.uptime, true)}</b></span>
          <span class="chip">SD card <b>{c.disk?.pct.toFixed(0)}%</b></span>
          <span class="chip">Load <b>{c.load?.[0].toFixed(2)}</b></span>
        </div>
      {/if}
      <p class="hint">Tap {pic ? "her" : store.anime === "kirino" ? "Pi-chan" : "the familiar"} to hear what {store.anime === "kirino" || pic ? "she" : "it"} thinks.
        <button type="button" class="underline decoration-dotted underline-offset-2 hover:text-ink" onclick={() => (store.artOpen = true)}>{pic ? "Change pictures" : "Add your own character pictures"}</button></p>
    </div>
  </div>
</section>
