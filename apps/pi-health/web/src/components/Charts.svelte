<script>
  import { store, RANGES } from "../lib/store.svelte.js";
  import { rate, rateStr, bytes } from "../lib/format.js";
  import Chart from "./Chart.svelte";
  import Heading from "./Heading.svelte";

  const h = $derived(store.hist);
  const s = $derived(store.state?.now ?? {});
  const now = $derived(store.now);
  const from = $derived(now - RANGES[store.range]);
  const pct = (x, a) => (x == null ? "–" : (a ? Math.round(x) : x.toFixed(x >= 10 ? 0 : 1)) + "%");
  const labels = { "5m": "5 min", "15m": "15 min", "1h": "1 hour", "6h": "6 hours", "24h": "24 hours" };
  let wide = $state(typeof window !== "undefined" && window.innerWidth >= 640);
  $effect(() => { const f = () => (wide = window.innerWidth >= 640); addEventListener("resize", f); return () => removeEventListener("resize", f); });
  const height = $derived(wide ? 180 : 150);

  const defs = $derived(h ? [
    { title: "CPU usage", now: s.cpu != null ? `${s.cpu.toFixed(0)}% at ${s.cpu_mhz} MHz` : "", series: [{ label: "CPU", values: h.cpu, color: "--c-s1" }], fmt: pct, yMax: 100, cores: true },
    { title: "Temperature", now: s.temp != null ? `${s.temp.toFixed(1)} °C` : "", series: [{ label: "Temperature", values: h.temp, color: "--c-s1" }], fmt: (x, a) => (x == null ? "–" : a ? `${Math.round(x)}°` : `${x.toFixed(1)} °C`), yMinAuto: true },
    { title: "Network traffic", now: `${rateStr(s.rx)} down`, series: [{ label: "Download", values: h.rx, color: "--c-s1" }, { label: "Upload", values: h.tx, color: "--c-s2" }], fmt: rateStr, axisFmt: (x) => { const [n, u] = rate(x); return `${n} ${u.replace("/s", "")}`; }, area: false },
    { title: "GPU activity", now: s.gpu != null ? `${s.gpu.toFixed(0)}% at ${s.gpu_mhz} MHz` : "", series: [{ label: "GPU busy", values: h.gpu, color: "--c-s1" }], fmt: pct, yMax: 100 },
    { title: "Power draw", est: true, now: s.watts != null ? `${s.watts.toFixed(2)} W` : "", series: [{ label: "Power", values: h.watts, color: "--c-s1" }], fmt: (x, a) => (x == null ? "–" : `${x.toFixed(a ? 0 : 2)} W`), nice: (v) => Math.max(5, Math.ceil(v)) },
    { title: "Memory used", now: s.mem_total ? `${bytes(s.mem_used)} of ${bytes(s.mem_total)}` : "", series: [{ label: "Memory", values: h.mem, color: "--c-s1" }], fmt: pct, yMax: 100 },
  ] : []);
</script>

<section aria-labelledby="hist-h">
  <div class="sticky top-[calc(56px+env(safe-area-inset-top))] z-10 -mx-4 mb-3 flex flex-wrap items-center gap-x-4 gap-y-2 bg-page/90 px-4 py-2 backdrop-blur-md lg:static lg:mx-0 lg:bg-transparent lg:px-0 lg:py-0 lg:backdrop-blur-none">
    <Heading key="history" id="hist-h" fallback="History" />
    <div class="flex w-full rounded-xl border border-line bg-panel p-1 sm:w-auto" role="group" aria-label="Time range">
      {#each Object.keys(RANGES) as r}
        <button type="button" aria-pressed={store.range === r} onclick={() => store.setRange(r)}
          class="flex-1 rounded-lg px-2.5 py-1.5 text-[13px] font-medium whitespace-nowrap transition sm:flex-none
                 {store.range === r ? 'bg-ink text-panel' : 'text-ink-2 hover:text-ink'}">{labels[r]}</button>
      {/each}
    </div>
  </div>

  <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
    {#each defs as d (d.title)}
      <article class="card min-w-0 p-4 pb-3">
        <header class="mb-1 flex items-baseline gap-2">
          <h3 class="flex items-center gap-1.5 text-[14.5px] font-semibold">{d.title}
            {#if d.est}<span class="rounded-md border border-line px-1.5 text-[10.5px] leading-4 font-normal text-ink-3">est.</span>{/if}
          </h3>
          <span class="ml-auto truncate text-[12.5px] text-ink-2">{d.now}</span>
        </header>
        <Chart t={h.t} series={d.series} fmt={d.fmt} axisFmt={d.axisFmt} yMax={d.yMax} yMinAuto={d.yMinAuto} nice={d.nice} area={d.area ?? true} {from} to={now} {height} />
        {#if d.cores && s.cores}
          <div class="mt-2 grid grid-cols-4 gap-2">
            {#each s.cores as v, i}
              <div class="text-[12px] text-ink-3">
                <div class="mb-1 h-1 overflow-hidden rounded-full bg-well"><div class="h-full rounded-full bg-s1 transition-[width] duration-500" style="width:{Math.min(v, 100)}%"></div></div>
                Core {i + 1} <span class="text-ink-2">{v.toFixed(0)}%</span>
              </div>
            {/each}
          </div>
        {/if}
      </article>
    {:else}
      {#each [1, 2, 3, 4] as _}<div class="card h-[230px] animate-pulse bg-well"></div>{/each}
    {/each}
  </div>
  <p class="mt-3 text-[12.5px] text-ink-3">
    {RANGES[store.range] > 3600 ? "One-minute averages. Temperature shows the peak of each minute." : "A reading every 2 seconds."} Touch or hover a chart to see exact values.
  </p>
</section>
