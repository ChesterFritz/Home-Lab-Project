<script>
  // "Where the money went": income sources → this month → spending categories (+ what was left).
  // Money is pooled in the middle node, so no source-to-category split is invented.
  import { sankey, sankeyLinkHorizontal, sankeyJustify } from "d3-sankey";
  import { animate, stagger } from "motion";
  import { peso, splitEmoji } from "../lib/fmt.js";
  import { reduced } from "../lib/motion.js";

  let { summary, monthLabel = "", onpick } = $props();
  let width = $state(0);
  let svg = $state();
  let hover = $state(null); // { kind: "link"|"node", i }
  let tip = $state(null);

  const MAX_OUT = 7;
  const MAX_IN = 4;

  function fold(list, max, otherName) {
    if (list.length <= max) return list;
    const head = list.slice(0, max - 1);
    const rest = list.slice(max - 1);
    return [...head, { id: "__other", name: otherName, amount: rest.reduce((s, x) => s + x.amount, 0), folded: rest.length }];
  }

  const layout = $derived.by(() => {
    if (!summary || width < 10 || (summary.income <= 0 && summary.expense <= 0)) return null;
    const narrow = width < 560;
    const ml = narrow ? 96 : 150;
    const mr = narrow ? 112 : 190;
    const ins = fold(summary.income_by_category, MAX_IN, "Other income");
    const outs = fold(summary.expense_by_category, MAX_OUT, "Everything else");
    const nodes = [];
    const links = [];
    const hub = { name: monthLabel || "This month", role: "hub" };
    ins.forEach((c) => nodes.push({ name: c.name, role: "in", id: c.id, amount: c.amount }));
    if (summary.net < 0) nodes.push({ name: "From balances", role: "draw", amount: -summary.net });
    const hubIndex = nodes.push(hub) - 1;
    outs.forEach((c) => nodes.push({ name: c.name, role: "out", id: c.id, amount: c.amount, folded: c.folded }));
    if (summary.net > 0) nodes.push({ name: "Left over", role: "kept", amount: summary.net });
    nodes.forEach((n, i) => {
      if (i < hubIndex) links.push({ source: i, target: hubIndex, value: n.amount });
      else if (i > hubIndex) links.push({ source: hubIndex, target: i, value: n.amount });
    });
    const h = Math.max(narrow ? 280 : 320, Math.min(520, nodes.length * (narrow ? 34 : 38)));
    const g = sankey()
      .nodeWidth(narrow ? 8 : 10)
      .nodePadding(narrow ? 12 : 14)
      .nodeAlign(sankeyJustify)
      .nodeSort(null)
      .extent([[ml, 8], [width - mr, h - 8]]);
    const res = g({ nodes: nodes.map((d) => ({ ...d })), links: links.map((d) => ({ ...d })) });
    // Two-line labels need ~32px; push neighbours apart within each column, then pull back inside.
    const GAP = 32;
    for (const side of ["left", "right"]) {
      const col = res.nodes
        .filter((n) => n.role !== "hub" && (side === "left") === n.x0 < width / 2)
        .sort((a, b) => a.y0 - b.y0);
      col.forEach((n, i) => {
        n.ly = (n.y0 + n.y1) / 2;
        if (i && n.ly - col[i - 1].ly < GAP) n.ly = col[i - 1].ly + GAP;
      });
      const over = (col.at(-1)?.ly ?? 0) - (h - 14);
      if (over > 0) {
        col.at(-1).ly -= over;
        for (let i = col.length - 2; i >= 0; i--) col[i].ly = Math.min(col[i].ly, col[i + 1].ly - GAP);
      }
    }
    return { ...res, h, narrow, total: Math.max(summary.income, summary.expense) };
  });

  const path = sankeyLinkHorizontal();
  const color = (role) =>
    ({ in: "var(--in)", kept: "var(--in)", out: "var(--out)", draw: "var(--xfer)", hub: "var(--ink)" })[role];
  const linkColor = (l) => (l.target.role === "hub" ? color(l.source.role) : color(l.target.role));

  // One orchestrated moment: the streams pour in left to right whenever the month's data arrives.
  let poured = null;
  let pourKey = $state(0);
  $effect(() => {
    if (!layout || !svg || reduced() || poured === summary) return;
    poured = summary; // a resize re-lays out but doesn't replay the pour
    pourKey++; // re-mounts the link group so the CSS pour replays
    const nodes = svg.querySelectorAll("[data-node]");
    const labels = svg.querySelectorAll("[data-label]");
    const a = [
      animate(nodes, { opacity: [0, 1], scaleY: [0.2, 1] }, { duration: 0.45, delay: stagger(0.03), ease: [0.22, 1, 0.36, 1] }),
      animate(labels, { opacity: [0, 1] }, { duration: 0.4, delay: stagger(0.03, { startDelay: 0.35 }) }),
    ];
    return () => a.forEach((x) => x.complete());
  });

  function share(v) {
    const t = layout?.total || 1;
    return Math.round((v / t) * 100);
  }

  function show(e, kind, i, text) {
    hover = { kind, i };
    const r = svg.getBoundingClientRect();
    tip = { x: e.clientX - r.left, y: e.clientY - r.top, text };
  }
  function hide() {
    hover = null;
    tip = null;
  }
  const dim = (kind, i, l) => {
    if (!hover) return false;
    if (hover.kind === "link") return !(kind === "link" && i === hover.i);
    const n = layout.nodes[hover.i];
    if (kind === "node") return i !== hover.i && n.role !== "hub" && layout.nodes[i].role !== "hub";
    return !(l.source.index === hover.i || l.target.index === hover.i || n.role === "hub");
  };
  const short = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
</script>

<div class="relative" bind:clientWidth={width}>
  {#if layout}
    <svg bind:this={svg} {width} height={layout.h} role="img" aria-label="Money flow: income on the left, spending on the right" class="block overflow-visible">
      {#key pourKey}
      <g fill="none">
        {#each layout.links as l, i}
          <path
            class="pour"
            style:animation-delay="{150 + i * 45}ms"
            d={path(l)}
            pathLength="1"
            stroke={linkColor(l)}
            stroke-width={Math.max(1.5, l.width)}
            stroke-opacity={dim("link", i, l) ? 0.1 : hover ? 0.55 : 0.3}
            role="presentation"
            onpointermove={(e) =>
              show(e, "link", i, `${l.source.role === "hub" ? l.target.name : l.source.name}: ${peso(l.value)}, ${share(l.value)}%`)}
            onpointerleave={hide}
          />
        {/each}
      </g>
      {/key}
      {#each layout.nodes as n, i}
        {@const left = n.x0 < width / 2 && n.role !== "hub"}
        {@const [emoji, plain] = splitEmoji(n.name)}
        {@const clickable = (n.role === "out" || n.role === "in") && n.id !== "__other"}
        <!-- svelte-ignore a11y_no_noninteractive_tabindex (role is "button" whenever tabindex is 0) -->
        <g
          class={clickable ? "cursor-pointer" : ""}
          role={clickable ? "button" : "presentation"}
          tabindex={clickable ? 0 : -1}
          aria-label={clickable ? `${n.name}, ${peso(n.value)}. Show transactions` : undefined}
          onclick={() => clickable && onpick?.(n)}
          onkeydown={(e) => clickable && (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onpick?.(n))}
          onpointerenter={() => (hover = { kind: "node", i })}
          onpointerleave={hide}
          opacity={dim("node", i) ? 0.35 : 1}
          style="transition: opacity .2s"
        >
          <rect
            data-node
            x={n.x0}
            y={n.y0}
            width={n.x1 - n.x0}
            height={Math.max(2, n.y1 - n.y0)}
            rx="3"
            fill={color(n.role)}
            style="transform-box: fill-box; transform-origin: center;"
          />
          {#if n.role === "hub"}
            <text data-label x={(n.x0 + n.x1) / 2} y={n.y0 - 2} dy="-0.4em" text-anchor="middle" class="fill-ink-2 text-[12px]" font-weight="600">{short(n.name, 18)}</text>
          {:else}
            {@const cy = (n.y0 + n.y1) / 2}
            {#if Math.abs(n.ly - cy) > 4}
              <path data-label d="M{left ? n.x0 - 2 : n.x1 + 2},{cy} L{left ? n.x0 - 7 : n.x1 + 7},{n.ly}" stroke="var(--line-strong)" fill="none" />
            {/if}
            <text data-label x={left ? n.x0 - 10 : n.x1 + 10} y={n.ly} text-anchor={left ? "end" : "start"} dominant-baseline="middle">
              <tspan x={left ? n.x0 - 10 : n.x1 + 10} dy="-0.55em" class="fill-ink text-[13px]" font-weight="600">{emoji ? emoji + " " : ""}{short(plain, layout.narrow ? 11 : 20)}</tspan>
              <tspan x={left ? n.x0 - 10 : n.x1 + 10} dy="1.25em" class="fill-ink-2 text-[12.5px] num">{peso(n.value, { whole: layout.narrow })}</tspan>
            </text>
          {/if}
        </g>
      {/each}
    </svg>
    {#if tip}
      <div
        class="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-[130%] whitespace-nowrap rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-on-primary"
        style="left:{tip.x}px; top:{tip.y}px"
      >
        {tip.text}
      </div>
    {/if}
  {/if}
</div>

<style>
  /* The pour: each stream draws from source to target, staggered. Reduced motion ends it instantly. */
  .pour {
    stroke-dasharray: 1 1;
    animation: pour 0.9s cubic-bezier(0.65, 0, 0.35, 1) both;
    transition: stroke-opacity 0.2s;
  }
  @keyframes pour {
    from { stroke-dashoffset: 1; }
    to { stroke-dashoffset: 0; }
  }
</style>
