<script>
  import { store } from "../lib/store.svelte.js";
  import { rate, bytes } from "../lib/format.js";
  import Sparkline from "./Sparkline.svelte";
  import { sfxFor, KAOMOJI } from "../lib/anime.js";

  const s = $derived(store.state?.now ?? {});
  const info = $derived(store.state?.info ?? {});
  const c = $derived(store.state?.checks ?? {});
  const L = $derived(store.live ?? {});
  const rx = $derived(rate(s.rx)), tx = $derived(rate(s.tx));
  const tempNote = (t) => (t >= 80 ? "Too hot" : t >= 70 ? "Hot" : t >= 60 ? "Warm" : "Normal");
  const fmt = (v, d = 0) => (v == null ? "–" : v.toFixed(d));
</script>

{#snippet fx(kind)}
  {#if store.anime}
    {@const word = sfxFor(kind, s)}
    {#if word}<span class="sfx-word" aria-hidden="true">{word}</span>{:else}<span class="kao" aria-hidden="true">{KAOMOJI[kind]}</span>{/if}
  {/if}
{/snippet}

{#snippet tile(label, value, unit, sub, spark, max, badge, kind)}
  <div class="vital card relative flex min-w-0 flex-col p-4 pb-3">
    {@render fx(kind)}
    <div class="flex items-center gap-1.5 text-[13px] text-ink-2">
      {label}
      {#if badge}<span class="rounded-md border border-line px-1.5 text-[10.5px] leading-4 text-ink-3" title="This board has no current sensor. Estimated from CPU load, clock speed, core voltage and GPU activity, within about 30%.">est.</span>{/if}
    </div>
    <div class="narrow mt-1.5 flex items-baseline gap-1 text-[34px] leading-none font-medium tracking-tight sm:text-[38px]">
      {value}<span class="text-[16px] font-normal text-ink-2" style="font-stretch:90%">{unit}</span>
    </div>
    <div class="mt-1.5 truncate text-[12.5px] text-ink-3">{sub}</div>
    <div class="mt-auto pt-2"><Sparkline values={spark ?? []} {max} /></div>
  </div>
{/snippet}

<section class="grid grid-cols-2 gap-3 md:grid-cols-3" aria-label="Current readings">
  {@render tile("CPU", fmt(s.cpu), "%", s.cpu_mhz ? `${s.cpu_mhz} MHz` : "", L.cpu, 100, false, "cpu")}
  {@render tile("Temperature", fmt(s.temp), "°C", s.temp != null ? tempNote(s.temp) : "", L.temp, null, false, "temp")}
  {@render tile("GPU", fmt(s.gpu), "%", s.gpu_mhz ? `${s.gpu_mhz} of ${info.gpu_max_mhz} MHz` : "", L.gpu, 100, false, "gpu")}
  {@render tile("Power", fmt(s.watts, 1), "W", s.watts != null ? `≈ ${Math.round((s.watts / 5) * 1000)} mA at 5 V` : "", L.watts, null, true, "power")}

  <div class="vital card relative flex min-w-0 flex-col p-4 pb-3">
    {@render fx("net")}
    <div class="text-[13px] text-ink-2">Network</div>
    <div class="narrow mt-1.5 grid gap-1 text-[24px] leading-none font-medium tracking-tight sm:text-[26px]">
      <div class="flex items-baseline gap-1"><span class="w-3 text-[14px] text-s1" style="font-stretch:100%">↓</span>{rx[0]}<span class="text-[13px] font-normal text-ink-2" style="font-stretch:90%">{rx[1]}</span></div>
      <div class="flex items-baseline gap-1"><span class="w-3 text-[14px] text-s2" style="font-stretch:100%">↑</span>{tx[0]}<span class="text-[13px] font-normal text-ink-2" style="font-stretch:90%">{tx[1]}</span></div>
    </div>
    <div class="mt-1.5 truncate text-[12.5px] text-ink-3">{c.link_mbps ? `${c.link_mbps} Mb/s link` : "Home network"}</div>
    <div class="mt-auto pt-2"><Sparkline values={L.rx ?? []} /></div>
  </div>

  {@render tile("Memory", fmt(s.mem), "%", s.mem_total ? `${bytes(s.mem_used)} of ${bytes(s.mem_total)}` : "", L.mem, 100, false, "mem")}
</section>
