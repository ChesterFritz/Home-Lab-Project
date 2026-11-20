<script>
  let { values = [], max = null, color = "var(--c-s1)" } = $props();
  const W = 120, H = 32;
  const path = $derived.by(() => {
    const v = values.filter((x) => x != null);
    if (v.length < 2) return null;
    const hi = max ?? Math.max(...v), lo = max != null ? 0 : Math.min(...v);
    const span = hi - lo || 1;
    const pts = v.map((n, i) => [(i / (v.length - 1)) * W, H - 2 - ((n - lo) / span) * (H - 4)]);
    const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join("");
    return { line, area: `${line}L${W},${H}L0,${H}Z` };
  });
</script>

<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" class="block h-8 w-full" aria-hidden="true">
  {#if path}
    <path d={path.area} fill={color} opacity="0.1" />
    <path d={path.line} fill="none" stroke={color} stroke-width="1.6" vector-effect="non-scaling-stroke" stroke-linejoin="round" />
  {/if}
</svg>
