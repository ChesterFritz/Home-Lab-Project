<script>
  import { store } from "../lib/store.svelte.js";
  import Icon from "./Icon.svelte";
  import Heading from "./Heading.svelte";

  const host = location.hostname || "192.168.18.28";
  const apps = $derived.by(() => {
    const st = store.state;
    if (!st) return [];
    const byName = Object.fromEntries((st.checks?.containers ?? []).map((x) => [x.name, x]));
    return (st.info?.links ?? []).map((l, i) => {
      const probe = (st.checks?.links ?? []).find((p) => p.i === i);
      const ct = l.container && byName[l.container];
      let state = "unknown", text = "External";
      if (probe && probe.up != null) { state = probe.up ? "up" : "down"; text = probe.up ? "Up" : "Down"; }
      if (ct && ct.state !== "running") { state = "down"; text = "Stopped"; }
      else if (ct?.health === "unhealthy") { state = "down"; text = "Unhealthy"; }
      return { ...l, url: l.url.replace("{host}", host), state, text };
    });
  });
  const dot = { up: "bg-good", down: "bg-critical", unknown: "border-[1.5px] border-ink-3" };
  const txt = { up: "text-good-ink", down: "text-critical-ink", unknown: "text-ink-3" };
</script>

<section aria-labelledby="apps-h">
  <div class="mb-3"><Heading key="apps" id="apps-h" fallback="Apps" /></div>
  <div class="grid grid-cols-2 gap-3">
    {#each apps as a (a.name)}
      <a href={a.url} target="_blank" rel="noopener" aria-label="Open {a.name}, {a.text}"
        class="card group flex min-w-0 flex-col gap-3 p-3.5 transition hover:border-ink-3 active:scale-[.98]">
        <div class="flex items-start justify-between gap-2">
          <span class="grid size-10 place-items-center rounded-xl bg-well text-ink"><Icon name={a.icon} size={21} /></span>
          <span class="flex items-center gap-1.5 rounded-full bg-well px-2 py-0.5 text-[12px] font-medium {txt[a.state]}">
            <span class="size-[7px] shrink-0 rounded-full {dot[a.state]}"></span>{a.text}
          </span>
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-1.5">
            <span class="truncate text-[14.5px] font-semibold">{a.name}</span>
            <Icon name="external" size={13} stroke={2} class="shrink-0 text-ink-3 transition group-hover:text-ink" />
          </div>
          <div class="mt-0.5 truncate text-[12.5px] text-ink-3" title={a.desc}>{a.desc}</div>
        </div>
      </a>
    {:else}
      {#each [1, 2, 3, 4] as _}<div class="card h-[104px] animate-pulse bg-well"></div>{/each}
    {/each}
  </div>
</section>
