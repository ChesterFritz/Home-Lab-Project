<script>
  // An original summoning circle: rings, a hexagram, rune ticks and a Latin-ish incantation
  // running round the rim. Used huge and faint behind the chuunibyou pages, and in bursts.
  let { size = 600, color = "#d42a48", gold = "#e8c46a", spin = true, uid = "mc" } = $props();
  const r = 46;
  const hex = (rot) =>
    Array.from({ length: 3 }, (_, i) => {
      const a = ((i * 120 + rot) * Math.PI) / 180;
      return `${50 + 34 * Math.cos(a)},${50 + 34 * Math.sin(a)}`;
    }).join(" ");
  const ticks = Array.from({ length: 48 }, (_, i) => (i * 360) / 48);
</script>

<svg viewBox="0 0 100 100" width={size} height={size} aria-hidden="true" style="overflow: visible">
  <defs>
    <path id="{uid}-rim" d="M50,50 m-{r - 4},0 a{r - 4},{r - 4} 0 1,1 {(r - 4) * 2},0 a{r - 4},{r - 4} 0 1,1 -{(r - 4) * 2},0" />
  </defs>
  <g class="magic-spin" style="transform-origin: 50px 50px; animation: {spin ? 'spin 90s linear infinite' : 'none'}">
    <circle cx="50" cy="50" r={r} fill="none" stroke={color} stroke-width=".5" />
    <circle cx="50" cy="50" r={r - 8} fill="none" stroke={color} stroke-width=".35" />
    {#each ticks as t, i}
      <line x1="50" y1={50 - r} x2="50" y2={50 - r + (i % 4 ? 1.4 : 3)} stroke={gold} stroke-width=".35" transform="rotate({t} 50 50)" />
    {/each}
    <text font-size="2.6" fill={gold} letter-spacing=".6" font-family="Cinzel, Georgia, serif">
      <textPath href="#{uid}-rim">✦ SIGNUM AURI ✦ VINCULUM ABYSSI ✦ OCULUS MALUS ✦ PACTUM SANGUINIS ✦ THESAURUS OBSIGNATUS ✦</textPath>
    </text>
  </g>
  <g class="magic-spin" style="transform-origin: 50px 50px; animation: {spin ? 'spin-back 60s linear infinite' : 'none'}">
    <polygon points={hex(-90)} fill="none" stroke={color} stroke-width=".55" />
    <polygon points={hex(90)} fill="none" stroke={color} stroke-width=".55" />
    <circle cx="50" cy="50" r="17" fill="none" stroke={gold} stroke-width=".4" />
    <circle cx="50" cy="50" r="12" fill="none" stroke={color} stroke-width=".3" stroke-dasharray="1 1.5" />
    <!-- the evil eye at the centre -->
    <path d="M41 50 Q50 43 59 50 Q50 57 41 50 Z" fill="none" stroke={gold} stroke-width=".5" />
    <circle cx="50" cy="50" r="2.6" fill={color} />
  </g>
</svg>
