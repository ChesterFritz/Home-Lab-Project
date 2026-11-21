<script>
  // A 12-month sparkline for a stat card. One series, so no legend; the card title names it.
  // The selected month gets a dot so the line connects to the number above it.
  import { scaleLinear, scalePoint } from "d3-scale";
  import { line, area, curveMonotoneX } from "d3-shape";
  import { animate } from "motion";
  import { reduced } from "../lib/motion.js";

  let { values = [], keys = [], selected = "", color = "var(--ink)", label = "" } = $props();
  let width = $state(0);
  const H = 44;

  const x = $derived(scalePoint().domain(keys).range([3, Math.max(4, width - 3)]));
  const y = $derived(scaleLinear().domain([Math.min(0, ...values), Math.max(1, ...values)]).range([H - 3, 4]));
  const pts = $derived(values.map((v, i) => [x(keys[i]), y(v)]));
  const d = $derived(line().curve(curveMonotoneX)(pts) ?? "");
  const fill = $derived(area().y0(H).curve(curveMonotoneX)(pts) ?? "");
  const sel = $derived(keys.indexOf(selected));
  let stroke = $state(), shade = $state(), dot = $state();
  $effect(() => {
    selected; values;
    if (!stroke || reduced()) return;
    const ease = [0.65, 0, 0.35, 1];
    animate(stroke, { strokeDashoffset: [1, 0] }, { duration: 1.1, ease });
    if (shade) animate(shade, { opacity: [0, 1] }, { duration: 0.8, delay: 0.4 });
    if (dot) animate(dot, { scale: [0, 1.6, 1] }, { duration: 0.5, delay: 1 });
  });
</script>

<div bind:clientWidth={width} class="h-11">
  {#if width && values.length > 1}
    <svg {width} height={H} role="img" aria-label={label} class="block overflow-visible">
      <path bind:this={shade} d={fill} fill={color} fill-opacity="0.12" />
      <path bind:this={stroke} {d} fill="none" stroke={color} stroke-width="2" stroke-linejoin="round" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1" />
      {#if sel >= 0}<circle bind:this={dot} style="transform-box: fill-box; transform-origin: center" cx={pts[sel][0]} cy={pts[sel][1]} r="3.5" fill={color} stroke="var(--card)" stroke-width="1.5" />{/if}
    </svg>
  {/if}
</div>
