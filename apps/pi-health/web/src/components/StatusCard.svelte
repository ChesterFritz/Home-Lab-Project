<script>
  import { store } from "../lib/store.svelte.js";
  import { dur, ago } from "../lib/format.js";
  import SevIcon from "./SevIcon.svelte";
  import AnimeStatus from "./anime/AnimeStatus.svelte";

  const st = $derived(store.state);
  const c = $derived(st?.checks ?? {});
  const alerts = $derived(st?.alerts ?? []);
  const offline = $derived(store.status === "offline");
  const sev = $derived(offline ? "offline" : alerts[0]?.severity ?? (st ? "good" : "info"));
  const checks = $derived((c.containers?.length ?? 0) + (c.links ?? []).filter((l) => l.up != null).length + 5);
  const tint = { good: "bg-panel", warning: "bg-warning-tint", serious: "bg-serious-tint", critical: "bg-critical-tint", offline: "bg-well", info: "bg-panel" };
  const label = { warning: "text-warning-ink", serious: "text-serious-ink", critical: "text-critical-ink" };
  const sinceLost = $derived(store.lastOk ? dur((Date.now() - store.lastOk) / 1000, true) : "");
</script>

{#if store.anime}
  <AnimeStatus />
{:else}
<section class="card overflow-hidden {tint[sev]}" aria-live="polite">
  <div class="flex gap-4 p-5 sm:p-6">
    <SevIcon sev={sev} size={40} />
    <div class="min-w-0 flex-1">
      {#if offline}
        <h1 class="wide text-[22px] leading-tight font-semibold tracking-tight text-balance sm:text-[28px]">Can't reach your Pi</h1>
        <p class="mt-1.5 text-[14.5px] text-ink-2">
          {sinceLost ? `Last reading ${sinceLost} ago. ` : ""}Check that it's powered on and that this device is on your home network or Tailscale. This page reconnects on its own.
        </p>
      {:else if alerts.length}
        <h1 class="wide text-[22px] leading-tight font-semibold tracking-tight text-balance sm:text-[28px]">{alerts[0].title}</h1>
        <p class="mt-1.5 text-[14.5px] {label[sev] ?? 'text-ink-2'}">
          {alerts[0].detail ? alerts[0].detail + ". " : ""}Started {dur(store.now - alerts[0].since, true)} ago.
        </p>
      {:else}
        <h1 class="wide text-[22px] leading-tight font-semibold tracking-tight text-balance sm:text-[28px]">
          {st ? "Everything's running normally" : "Checking your Pi…"}
        </h1>
        <p class="mt-1.5 text-[14.5px] text-ink-2">
          {c.t ? `${checks} checks passed, last checked ${ago(c.t, store.now)}.` : "Waiting for the first reading."}
        </p>
      {/if}

      {#if alerts.length > 1 && !offline}
        <ul class="mt-3 space-y-1.5">
          {#each alerts.slice(1) as a (a.key)}
            <li class="flex items-center gap-2 text-[14px]">
              <SevIcon sev={a.severity} size={16} /><span class="min-w-0 flex-1 truncate">{a.title}</span>
              <span class="shrink-0 text-[12.5px] text-ink-3">{dur(store.now - a.since)}</span>
            </li>
          {/each}
        </ul>
      {/if}

      {#if c.uptime}
        <dl class="mt-4 flex flex-wrap gap-2 text-[12.5px]">
          <div class="rounded-lg bg-well px-2.5 py-1"><dt class="inline text-ink-3">Up for</dt> <dd class="inline font-semibold">{dur(c.uptime, true)}</dd></div>
          <div class="rounded-lg bg-well px-2.5 py-1"><dt class="inline text-ink-3">SD card</dt> <dd class="inline font-semibold">{c.disk?.pct.toFixed(0)}% used</dd></div>
          <div class="rounded-lg bg-well px-2.5 py-1"><dt class="inline text-ink-3">Load</dt> <dd class="inline font-semibold">{c.load?.[0].toFixed(2)}</dd></div>
        </dl>
      {/if}
    </div>
  </div>
</section>
{/if}
