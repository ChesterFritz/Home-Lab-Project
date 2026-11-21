<script>
  // Viking theme scenery: aurora, moon, mountains, a fjord with a longship, a dragon that flies past,
  // and rising embers mixed with falling snow (canvas). All decorative, behind the cards, no pointer events.
  // flyby: bump the number to send the dragon across right now. storm: a lightning flash (alerts).
  import { onMount } from "svelte";
  let { boost = 0, flyby = 0, storm = 0 } = $props();
  let canvas;
  let dragonKey = $state(0);
  let flash = $state(0);

  $effect(() => { if (flyby) dragonKey++; });
  $effect(() => { if (storm) { flash++; } });

  onMount(() => {
    // The dragon also passes on its own every couple of minutes.
    const t = setInterval(() => { if (!document.hidden) dragonKey++; }, 110000);
    const first = setTimeout(() => dragonKey++, 6000);
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return () => { clearInterval(t); clearTimeout(first); };

    const g = canvas.getContext("2d");
    let W, H, raf, items = [];
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const resize = () => { W = innerWidth; H = innerHeight; canvas.width = W * dpr; canvas.height = H * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0); };
    resize(); addEventListener("resize", resize);
    const spawn = (anywhere) => {
      const ember = Math.random() < .62;
      return ember
        ? { ember, x: Math.random() * W, y: anywhere ? Math.random() * H : H + 10, r: .8 + Math.random() * 2.2, vy: -(.35 + Math.random() * .9),
            vx: (Math.random() - .5) * .3, sway: Math.random() * 6.28, life: 1, fade: .0016 + Math.random() * .003, hue: Math.random() }
        : { ember, x: Math.random() * W, y: anywhere ? Math.random() * H : -10, r: .8 + Math.random() * 1.8, vy: .3 + Math.random() * .6,
            vx: (Math.random() - .2) * .4, sway: Math.random() * 6.28, life: 1, fade: 0, hue: 0 };
    };
    const target = () => Math.round((W < 700 ? 34 : 60) * (1 + boost));
    for (let i = 0; i < target(); i++) items.push(spawn(true));

    const tick = () => {
      g.clearRect(0, 0, W, H);
      while (items.length < target()) items.push(spawn(false));
      for (const p of items) {
        p.sway += .03; p.x += p.vx + Math.sin(p.sway) * (p.ember ? .35 : .5); p.y += p.vy; p.life -= p.fade;
        if (p.ember) {
          const a = Math.max(0, p.life) * (.6 + Math.sin(p.sway * 3) * .25);
          const c = p.hue < .5 ? "255,140,40" : p.hue < .85 ? "255,200,90" : "255,90,30";
          g.beginPath(); g.arc(p.x, p.y, p.r * 2.6, 0, 6.28); g.fillStyle = `rgba(${c},${a * .18})`; g.fill();
          g.beginPath(); g.arc(p.x, p.y, p.r, 0, 6.28); g.fillStyle = `rgba(${c},${a})`; g.fill();
        } else {
          g.beginPath(); g.arc(p.x, p.y, p.r, 0, 6.28); g.fillStyle = "rgba(230,240,255,.75)"; g.fill();
        }
      }
      items = items.filter((p) => p.life > 0 && p.y > -20 && p.y < H + 20 && p.x > -20 && p.x < W + 20);
      raf = requestAnimationFrame(tick);
    };
    const vis = () => { cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(tick); };
    document.addEventListener("visibilitychange", vis);
    raf = requestAnimationFrame(tick);
    return () => { clearInterval(t); clearTimeout(first); cancelAnimationFrame(raf); removeEventListener("resize", resize); document.removeEventListener("visibilitychange", vis); };
  });
</script>

<div class="sky" aria-hidden="true">
  <div class="aurora a1"></div><div class="aurora a2"></div><div class="aurora a3"></div>
  <div class="moon"></div>

  {#key dragonKey}
    {#if dragonKey}
      <svg class="dragon" viewBox="0 -16 200 116">
        <g class="dwing back"><path d="M96 50 Q84 18 66 -6 L88 8 L96 -12 L108 10 L124 2 L120 48 Z" /></g>
        <path d="M58 56 Q88 44 120 50 Q134 53 140 47 Q148 38 162 36 L176 37 L184 41 L170 44 Q156 46 146 58 Q124 68 92 64 Q70 64 58 58 Z" />
        <path d="M80 51 Q52 49 30 45 Q18 46 3 41 L9 48 L2 53 Q14 47 26 52 Q46 61 80 61 Z" />
        <path d="M163 36 L156 26 L167 33 Z M170 36 L166 27 L174 34 Z" />
        <path d="M92 63 L88 76 L94 74 L96 63 Z M120 62 L118 75 L124 73 L125 61 Z" />
        <circle cx="172" cy="40" r="1.4" class="eye" />
        <g class="dwing front"><path d="M100 50 Q88 14 70 -12 L94 4 L102 -15 L114 8 L132 -2 L126 48 Z" /></g>
      </svg>
    {/if}
  {/key}

  <svg class="mountains far" viewBox="0 0 1200 220" preserveAspectRatio="none">
    <path d="M0 220 L0 140 L80 90 L150 130 L240 60 L330 120 L420 80 L500 130 L600 50 L700 120 L790 70 L880 130 L960 85 L1050 125 L1130 75 L1200 110 L1200 220 Z" />
    <path class="snow" d="M240 60 L262 78 L250 76 L238 84 L226 74 Z M600 50 L626 72 L612 70 L598 80 L584 68 Z M790 70 L810 86 L798 85 L786 92 L776 82 Z M1130 75 L1150 90 L1138 89 L1128 96 L1118 86 Z M80 90 L96 102 L86 101 L76 106 L68 100 Z" />
  </svg>
  <svg class="mountains near" viewBox="0 0 1200 200" preserveAspectRatio="none">
    <path d="M0 200 L0 120 L110 70 L190 110 L300 40 L380 100 L470 75 L560 125 L680 60 L760 105 L860 55 L960 115 L1060 80 L1200 130 L1200 200 Z" />
    <path class="snow" d="M300 40 L326 62 L312 60 L300 70 L286 58 Z M860 55 L884 74 L871 73 L860 81 L848 70 Z M680 60 L700 76 L690 75 L680 82 L670 74 Z" />
  </svg>
  <div class="sea">
    <svg class="waves w1" viewBox="0 0 400 20" preserveAspectRatio="none"><path d="M0 10 Q25 0 50 10 T100 10 T150 10 T200 10 T250 10 T300 10 T350 10 T400 10 V20 H0 Z" /></svg>
    <div class="ship-lane">
      <svg class="ship" viewBox="0 0 220 110">
        <g class="oars"><path d="M60 78 L46 102 M80 78 L66 102 M100 78 L86 102 M120 78 L106 102 M140 78 L126 102 M160 78 L146 102" /></g>
        <rect x="107" y="4" width="5" height="70" class="mast" />
        <clipPath id="sail-clip"><path d="M66 10 L154 10 Q160 36 152 58 L68 58 Q60 36 66 10 Z" /></clipPath>
        <g clip-path="url(#sail-clip)" class="sail">
          <rect x="60" y="8" width="104" height="54" fill="#efe3c8" />
          {#each [0, 1, 2, 3, 4, 5] as i}<rect x={62 + i * 17.5} y="8" width="9" height="54" fill="#b3261e" />{/each}
        </g>
        <path d="M66 10 L154 10 Q160 36 152 58 L68 58 Q60 36 66 10 Z" fill="none" stroke="#1a0f08" stroke-width="2.5" />
        <path d="M14 62 Q26 86 64 86 L156 86 Q194 86 206 62 L196 66 Q186 76 156 76 L64 76 Q34 76 24 66 Z" class="hull" />
        <path d="M204 64 Q218 40 210 20 Q204 10 196 14 Q192 20 200 22 Q206 30 198 52 Z" class="hull" />
        <circle cx="199" cy="18" r="2" fill="#ffb020" />
        <path d="M16 64 Q2 44 10 28 Q14 22 20 26 Q12 34 22 56 Z" class="hull" />
        {#each [0, 1, 2, 3, 4, 5, 6, 7] as i}
          <circle cx={52 + i * 16} cy="72" r="6.5" fill={["#b3261e", "#e8b04a", "#efe3c8", "#2f6f8f"][i % 4]} stroke="#1a0f08" stroke-width="1.8" />
          <circle cx={52 + i * 16} cy="72" r="1.8" fill="#1a0f08" />
        {/each}
      </svg>
    </div>
    <svg class="waves w2" viewBox="0 0 400 20" preserveAspectRatio="none"><path d="M0 10 Q25 2 50 10 T100 10 T150 10 T200 10 T250 10 T300 10 T350 10 T400 10 V20 H0 Z" /></svg>
  </div>
  {#key flash}{#if flash}<div class="lightning"></div>{/if}{/key}
</div>
<canvas bind:this={canvas} class="pointer-events-none fixed inset-0 z-[5] h-full w-full" aria-hidden="true"></canvas>

<style>
  .sky { position: fixed; inset: 0; z-index: 1; pointer-events: none; overflow: hidden; --ground: 0px; }
  /* Phones and tablets have a bottom tab bar; lift the land and sea above it. */
  @media (max-width: 1023px) { .sky { --ground: calc(60px + env(safe-area-inset-bottom)); } }

  .aurora { position: absolute; left: -20%; width: 140%; height: 46vh; top: -8vh; filter: blur(38px); mix-blend-mode: screen; opacity: .55; }
  .a1 { background: linear-gradient(100deg, transparent 10%, rgba(60, 255, 180, .55) 30%, rgba(80, 200, 255, .35) 50%, transparent 70%);
    clip-path: polygon(0 40%, 20% 20%, 40% 45%, 60% 15%, 80% 40%, 100% 20%, 100% 60%, 80% 75%, 60% 50%, 40% 80%, 20% 55%, 0 75%); animation: drift 26s ease-in-out infinite alternate; }
  .a2 { top: 0; background: linear-gradient(80deg, transparent 20%, rgba(150, 90, 255, .45) 45%, rgba(60, 255, 170, .35) 60%, transparent 80%);
    clip-path: polygon(0 30%, 25% 50%, 50% 25%, 75% 55%, 100% 30%, 100% 55%, 75% 80%, 50% 50%, 25% 75%, 0 55%); animation: drift 34s ease-in-out infinite alternate-reverse; }
  .a3 { top: 6vh; opacity: .35; background: linear-gradient(90deg, transparent, rgba(60, 255, 200, .6) 50%, transparent);
    clip-path: polygon(0 50%, 30% 40%, 60% 55%, 100% 45%, 100% 52%, 60% 62%, 30% 48%, 0 58%); animation: drift 19s ease-in-out infinite alternate; }
  @keyframes drift { 0% { transform: translateX(-6%) skewX(-6deg); } 100% { transform: translateX(6%) skewX(6deg); } }

  .moon { position: absolute; right: 9%; top: 9vh; width: 64px; height: 64px; border-radius: 50%;
    background: radial-gradient(circle at 38% 38%, #fffaf0, #e9e1cf 60%, #c9bfa8); box-shadow: 0 0 40px 12px rgba(255, 245, 220, .18), 0 0 120px 40px rgba(160, 200, 255, .08); }
  .moon::after { content: ""; position: absolute; inset: 0; border-radius: 50%;
    background: radial-gradient(circle at 62% 60%, rgba(150, 140, 120, .35) 0 6px, transparent 7px), radial-gradient(circle at 35% 66%, rgba(150, 140, 120, .3) 0 4px, transparent 5px), radial-gradient(circle at 55% 30%, rgba(150, 140, 120, .25) 0 3px, transparent 4px); }

  .mountains { position: absolute; left: 0; width: 100%; }
  .mountains.far { bottom: calc(var(--ground) + 9vh); height: 24vh; fill: #16283a; }
  .mountains.near { bottom: calc(var(--ground) + 6vh); height: 18vh; fill: #0c1822; }
  .mountains .snow { fill: #cfe3f2; opacity: .8; }
  .mountains.near .snow { opacity: .55; }

  .sea { position: absolute; left: 0; right: 0; bottom: 0; height: calc(var(--ground) + 8vh); background: linear-gradient(180deg, #0f2a3a, #07131b); }
  .waves { position: absolute; left: 0; width: 200%; height: 14px; }
  .waves.w1 { top: -10px; fill: #123246; animation: waves 14s linear infinite; }
  .waves.w2 { bottom: 0; height: 22px; fill: #0a1c27; animation: waves 9s linear infinite reverse; opacity: .9; }
  @keyframes waves { to { transform: translateX(-50%); } }

  .ship-lane { position: absolute; left: 0; right: 0; bottom: calc(var(--ground) + 2.4vh); height: 0; }
  .ship { position: absolute; bottom: -10px; width: 150px; left: -170px; animation: sail 95s linear infinite, bob 3.4s ease-in-out infinite; filter: drop-shadow(0 3px 4px rgba(0, 0, 0, .5)); }
  .ship .hull { fill: #5a3418; stroke: #1a0f08; stroke-width: 2.5; stroke-linejoin: round; }
  .ship .mast { fill: #3a2410; }
  .ship .oars path { stroke: #c9a774; stroke-width: 2.5; stroke-linecap: round; }
  .oars { transform-origin: 110px 78px; animation: row 2.2s ease-in-out infinite; }
  @keyframes sail { to { left: calc(100% + 20px); } }
  @keyframes bob { 0%, 100% { transform: translateY(0) rotate(-1.5deg); } 50% { transform: translateY(-4px) rotate(1.5deg); } }
  @keyframes row { 0%, 100% { transform: skewX(0); } 50% { transform: skewX(22deg); } }

  .dragon { position: absolute; top: 14vh; left: -260px; width: 220px; fill: #071017; opacity: .92;
    filter: drop-shadow(0 0 14px rgba(60, 255, 190, .25)); animation: fly 16s cubic-bezier(.4, .1, .6, .9) forwards; }
  .dragon .eye { fill: #ffb020; }
  .dwing { transform-origin: 104px 50px; animation: flapw .7s ease-in-out infinite; }
  .dwing.back { opacity: .7; animation-delay: -.08s; }
  @keyframes flapw { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(-.55); } }
  @keyframes fly {
    0% { transform: translate(0, 0) rotate(4deg); }
    30% { transform: translate(40vw, -6vh) rotate(-3deg); }
    60% { transform: translate(78vw, 4vh) rotate(5deg); }
    100% { transform: translate(calc(100vw + 300px), -10vh) rotate(-6deg); }
  }

  .lightning { position: absolute; inset: 0; background: rgba(210, 235, 255, .55); animation: strike 1s ease-out forwards; }
  @keyframes strike { 0% { opacity: 0; } 6% { opacity: 1; } 12% { opacity: .1; } 18% { opacity: .85; } 40%, 100% { opacity: 0; } }

  @media (max-width: 700px) {
    .moon { width: 44px; height: 44px; right: 7%; }
    .ship { width: 110px; }
    .dragon { width: 150px; top: 18vh; }
  }
  @media (prefers-reduced-motion: reduce) {
    .aurora, .waves, .ship, .oars, .dwing { animation: none; }
    .ship { left: 12%; }
    .dragon { display: none; }
  }
</style>
