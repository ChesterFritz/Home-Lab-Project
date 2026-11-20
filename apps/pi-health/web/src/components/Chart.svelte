<script>
  import uPlot from "uplot";
  import { onMount } from "svelte";
  import { store } from "../lib/store.svelte.js";

  // series: [{ label, values, color: "--c-s1" }]
  let { t = [], series = [], fmt = (v) => v, axisFmt = null, yMax = null, yMinAuto = false, nice = null, from, to, height = 170, area = true } = $props();
  let el, u, ro;

  const v = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  function build() {
    u?.destroy();
    const ink3 = v("--c-ink-3"), grid = v("--c-grid");
    const axis = { stroke: ink3, grid: { stroke: grid, width: 1 }, ticks: { show: false }, font: `12px ${getComputedStyle(document.body).fontFamily}`, gap: 6 };
    const opts = {
      width: el.clientWidth, height,
      padding: [8, 6, 0, 0],
      cursor: { y: false, points: { size: 8, width: 2, stroke: v("--c-panel") }, drag: { x: false, y: false } },
      legend: { show: false },
      plugins: [tooltip()],
      scales: {
        x: { time: true, range: () => [from, to] },
        y: { range: (u, lo, hi) => {
          if (yMax != null) return [0, yMax];
          if (yMinAuto) return [Math.floor((lo ?? 0) - 2), Math.ceil((hi ?? 1) + 2)];
          const top = nice ? nice(hi ?? 0) : uPlot.rangeNum(0, Math.max(hi ?? 0, 1e-9), 0.1, true)[1];
          return [0, top];
        } },
      },
      axes: [
        { ...axis, space: 72, values: (u, splits) => splits.map((ts) => hm(ts, to - from > 20 * 3600)) },
        { ...axis, size: 48, values: (u, vals) => vals.map((x) => (axisFmt ?? fmt)(x, true)), splits: (u, i, lo, hi) => [0, 1, 2, 3].map((k) => lo + ((hi - lo) * k) / 3) },
      ],
      series: [
        { value: (u, ts) => (ts == null ? "Now" : new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })) },
        ...series.map((s, i) => ({
          label: s.label, stroke: v(s.color), _stroke: v(s.color), width: 2, spanGaps: false, points: { show: false },
          fill: area && series.length === 1 ? v("--c-s1-fill") : undefined,
          value: (u, x) => (x == null ? "–" : fmt(x)),
        })),
      ],
    };
    u = new uPlot(opts, data(), el);
  }
  const data = () => [t, ...series.map((s) => s.values)];
  const hm = (ts, day) => new Date(ts * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const stamp = (ts) => new Date(ts * 1000).toLocaleString([], to - from > 20 * 3600
    ? { weekday: "short", hour: "numeric", minute: "2-digit" } : { hour: "numeric", minute: "2-digit", second: "2-digit" });

  // Hover / touch tooltip that follows the cursor line.
  function tooltip() {
    let tip;
    return { hooks: {
      init: (u) => { tip = document.createElement("div"); tip.className = "ph-tip"; u.over.appendChild(tip); },
      setCursor: (u) => {
        const i = u.cursor.idx;
        if (i == null || u.data[0][i] == null) { tip.style.display = "none"; return; }
        let rows = "";
        u.series.forEach((s, k) => {
          if (!k) return;
          const val = u.data[k][i];
          rows += `<div class="r"><i style="background:${s._stroke ?? s.stroke()}"></i>${s.label}<b>${val == null ? "–" : fmt(val)}</b></div>`;
        });
        tip.innerHTML = `<div class="h">${stamp(u.data[0][i])}</div>${rows}`;
        tip.style.display = "block";
        const x = u.valToPos(u.data[0][i], "x"), w = tip.offsetWidth, W = u.over.clientWidth;
        tip.style.left = (x + 12 + w > W ? Math.max(x - w - 12, 0) : x + 12) + "px";
      },
    } };
  }

  onMount(() => {
    build();
    ro = new ResizeObserver(() => u && el.clientWidth && u.setSize({ width: el.clientWidth, height }));
    ro.observe(el);
    return () => { ro.disconnect(); u?.destroy(); };
  });

  $effect(() => { data(); from; to; if (u) u.setData(data()); });   // new samples
  $effect(() => { store.theme; height; if (u) build(); });          // theme or size change
  $effect(() => {
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const h = () => u && build();
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  });
</script>

<div bind:this={el} class="w-full min-w-0"></div>
