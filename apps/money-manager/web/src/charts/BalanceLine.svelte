<script>
  // One balance over time: 2px line, soft area to zero, emphasized zero line, crosshair + tooltip.
  import { scaleLinear, scalePoint } from "d3-scale";
  import { line, area, curveMonotoneX } from "d3-shape";
  import { animate } from "motion";
  import { peso, pesoShort } from "../lib/fmt.js";
  import { reduced } from "../lib/motion.js";

  let { points = [], label = (p) => p.key, tick = label, height = 200, name = "Balance" } = $props();
  let width = $state(0);
  let hover = $state(-1);
  let linePath = $state();
  const M = { t: 12, r: 10, b: 24, l: 50 };

  const ext = $derived.by(() => {
    const v = points.map((p) => p.value);
    let lo = Math.min(0, ...v), hi = Math.max(0, ...v);
    if (hi - lo < 1000) hi = lo + 1000; // a flat or tiny line still gets whole-peso ticks
    return [lo, hi];
  });
  const y = $derived(scaleLinear().domain(ext).nice(4).range([height - M.b, M.t]));
  const x = $derived(scalePoint().domain(points.map((p) => p.key)).range([M.l, Math.max(M.l + 1, width - M.r)]));
  const d = $derived(line().x((p) => x(p.key)).y((p) => y(p.value)).curve(curveMonotoneX)(points) ?? "");
  const fill = $derived(area().x((p) => x(p.key)).y0(y(0)).y1((p) => y(p.value)).curve(curveMonotoneX)(points) ?? "");
  const ticks = $derived(y.ticks(4));
  const every = $derived(Math.max(1, Math.ceil(points.length / Math.max(2, Math.floor(width / 70)))));
  const last = $derived(points.at(-1));

  let drawn = null;
  $effect(() => {
    if (!linePath || !d || reduced() || drawn === points) return;
    drawn = points;
    const a = animate(linePath, { strokeDashoffset: [1, 0] }, { duration: 1, ease: [0.65, 0, 0.35, 1] });
    return () => a.complete();
  });

  function move(e) {
    // Measure against the whole chart, not the hit rectangle (which starts at the left margin).
    const r = e.currentTarget.ownerSVGElement.getBoundingClientRect();
    const px = e.clientX - r.left;
    let best = 0;
    points.forEach((p, i) => {
      if (Math.abs(x(p.key) - px) < Math.abs(x(points[best].key) - px)) best = i;
    });
    hover = best;
  }
</script>

<div class="relative select-none" bind:clientWidth={width}>
  {#if width && points.length}
    <svg {width} {height} role="img" aria-label="{name} over time, now {peso(last.value)}" class="block overflow-visible">
      {#each ticks as t}
        <line x1={M.l} x2={width - M.r} y1={y(t)} y2={y(t)} stroke={t === 0 ? "var(--line-strong)" : "var(--line)"} stroke-width={t === 0 ? 1.5 : 1} />
        <text x={M.l - 8} y={y(t)} text-anchor="end" dominant-baseline="middle" class="fill-muted text-[11px] num">{t === 0 ? "0" : pesoShort(t)}</text>
      {/each}
      {#each points as p, i (p.key)}
        {#if i === points.length - 1 || (i % every === 0 && points.length - 1 - i >= every)}
          <text x={x(p.key)} y={height - 6} text-anchor={i === points.length - 1 ? "end" : i === 0 ? "start" : "middle"} class="fill-muted text-[11px]">{tick(p)}</text>
        {/if}
      {/each}
      <path d={fill} fill="var(--xfer)" fill-opacity="0.1" />
      <path bind:this={linePath} {d} fill="none" stroke="var(--xfer)" stroke-width="2" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" />
      <circle cx={x(last.key)} cy={y(last.value)} r="4.5" fill="var(--xfer)" stroke="var(--card)" stroke-width="2" />
      {#if hover >= 0}
        {@const p = points[hover]}
        <line x1={x(p.key)} x2={x(p.key)} y1={M.t} y2={height - M.b} stroke="var(--line-strong)" />
        <circle cx={x(p.key)} cy={y(p.value)} r="5" fill="var(--xfer)" stroke="var(--card)" stroke-width="2" />
      {/if}
      <rect
        x={M.l - 10}
        y="0"
        width={Math.max(0, width - M.l)}
        {height}
        fill="transparent"
        role="presentation"
        onpointermove={move}
        onpointerdown={move}
        onpointerleave={() => (hover = -1)}
      />
    </svg>
    {#if hover >= 0}
      {@const p = points[hover]}
      <div
        class="pointer-events-none absolute top-0 z-10 w-max rounded-xl bg-primary px-3 py-1.5 text-sm text-on-primary"
        style="left:{Math.min(Math.max(x(p.key), 70), width - 70)}px; transform: translateX(-50%)"
      >
        <span class="opacity-80">{label(p)}</span> <span class="num font-semibold">{peso(p.value)}</span>
      </div>
    {/if}
  {/if}
</div>
