<script>
  // Money in rises above the line, money out hangs below it: one column per month, mirrored.
  // 2px gap at the zero line, 4px rounded data-ends.
  import { scaleBand, scaleLinear } from "d3-scale";
  import { Tween, prefersReducedMotion } from "svelte/motion";
  import { cubicOut } from "svelte/easing";
  import { peso, pesoShort, monthShort, monthName } from "../lib/fmt.js";

  let { data = [], selected = "", onselect } = $props();
  let width = $state(0);
  let hover = $state(-1);
  const H = 280;
  const M = { t: 10, r: 4, b: 26, l: 46 };

  const values = new Tween([], { duration: 650, easing: cubicOut });
  $effect(() => {
    const v = data.map((d) => [d.income, d.expense]);
    values.set(v, { duration: prefersReducedMotion.current || values.current.length !== v.length ? 0 : 650 });
  });

  const max = $derived(Math.max(1, ...data.flatMap((d) => [d.income, d.expense])));
  const y = $derived(scaleLinear().domain([-max, max]).nice(4).range([H - M.b, M.t]));
  const x = $derived(scaleBand().domain(data.map((d) => d.month)).range([M.l, Math.max(M.l + 1, width - M.r)]).paddingInner(0.28).paddingOuter(0.1));
  const bw = $derived(Math.max(3, Math.min(26, x.bandwidth())));

  // Bar anchored 1px off the zero line, rounded only at its data end (up for in, down for out).
  function bar(x0, w, v, dir) {
    const base = y(0) - dir;
    const end = y(dir * Math.max(0, v));
    const h = Math.abs(base - end);
    if (v <= 0 || h < 0.5) return "";
    const r = Math.min(4, w / 2, h);
    const e = end + dir * r; // where the rounding starts
    return `M${x0},${base}V${e}Q${x0},${end} ${x0 + r},${end}H${x0 + w - r}Q${x0 + w},${end} ${x0 + w},${e}V${base}Z`;
  }
  const ticks = $derived(y.ticks(4));
  const labelEvery = $derived(width < 480 ? 2 : 1);
</script>

<div class="relative select-none" bind:clientWidth={width}>
  {#if width}
    <svg {width} height={H} role="img" aria-label="Money in and money out for the last {data.length} months" class="block">
      {#each ticks as t}
        <line x1={M.l} x2={width - M.r} y1={y(t)} y2={y(t)} stroke={t === 0 ? "var(--line-strong)" : "var(--line)"} stroke-width="1" />
        <text x={M.l - 8} y={y(t)} text-anchor="end" dominant-baseline="middle" class="fill-muted text-[11px] num">{t === 0 ? "0" : pesoShort(Math.abs(t))}</text>
      {/each}
      {#each data as d, i (d.month)}
        {@const x0 = x(d.month)}
        {@const cx = x0 + x.bandwidth() / 2}
        {@const v = values.current[i] ?? [0, 0]}
        {@const isSel = d.month === selected}
        {#if isSel}<rect x={x0 - (x.step() - x.bandwidth()) / 2 + 2} y={M.t} width={x.step() - 4} height={H - M.t - M.b} rx="10" fill="var(--inset)" class="pointer-events-none" />{/if}
        <g opacity={hover >= 0 && hover !== i ? 0.45 : 1} style="transition: opacity .15s">
          <path d={bar(cx - bw / 2, bw, v[0], 1)} fill="var(--in)" />
          <path d={bar(cx - bw / 2, bw, v[1], -1)} fill="var(--out)" />
        </g>
        {#if i % labelEvery === 0 || isSel}
          <text x={cx} y={H - 8} text-anchor="middle" class="text-[11.5px] {isSel ? 'fill-ink' : 'fill-muted'}" font-weight={isSel ? 700 : 400}>{monthShort(d.month)}</text>
        {/if}
        <!-- Hit target: the whole month band, taller and wider than the bars. -->
        <rect
          x={x0 - (x.step() - x.bandwidth()) / 2}
          y={M.t}
          width={x.step()}
          height={H - M.t - M.b + 22}
          fill="transparent"
          class="cursor-pointer"
          role="button"
          tabindex="0"
          aria-label="{monthName(d.month)}: in {peso(d.income)}, out {peso(d.expense)}"
          onpointerenter={() => (hover = i)}
          onpointerleave={() => (hover = -1)}
          onfocus={() => (hover = i)}
          onblur={() => (hover = -1)}
          onclick={() => onselect?.(d.month)}
          onkeydown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onselect?.(d.month))}
        />
      {/each}
    </svg>
    {#if hover >= 0 && data[hover]}
      {@const d = data[hover]}
      {@const cx = x(d.month) + x.bandwidth() / 2}
      <div
        class="pointer-events-none absolute top-0 z-10 w-max rounded-xl bg-primary px-3 py-2 text-sm text-on-primary"
        style="left:{Math.min(Math.max(cx, 90), width - 90)}px; transform: translateX(-50%)"
      >
        <div class="font-semibold">{monthName(d.month)}</div>
        <div class="num grid grid-cols-[auto_auto] gap-x-3">
          <span class="flex items-center gap-1.5"><i class="size-2 rounded-[2px] bg-in"></i>In</span><span class="text-right">{peso(d.income)}</span>
          <span class="flex items-center gap-1.5"><i class="size-2 rounded-[2px] bg-out"></i>Out</span><span class="text-right">{peso(d.expense)}</span>
          <span class="opacity-75">Net</span><span class="text-right opacity-75">{peso(d.income - d.expense, { sign: true })}</span>
        </div>
      </div>
    {/if}
  {/if}
</div>
