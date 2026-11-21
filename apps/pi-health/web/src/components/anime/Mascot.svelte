<script>
  // Pi-chan: an original mascot — the Orange Pi's chip with anime eyes.
  // mood: happy | normal | worried | angry | dizzy ; flavor: kirino (bow) | kuroneko (cat ears) | viking (a little dragon in a horned helmet)
  let { mood = "normal", flavor = "kirino", size = 96, onpoke = null } = $props();
  let squish = $state(false);
  const k = $derived(flavor === "kuroneko");
  const v = $derived(flavor === "viking");
  const body = $derived(v ? "#2fa38c" : k ? "#2b2038" : "#ff8a1f");
  const bodyHi = $derived(v ? "#7fe0c4" : k ? "#3d2d50" : "#ffb15c");
  const ink = $derived(v ? "#0d1c22" : k ? "#0d0812" : "#3a1030");
  const iris = $derived(v ? "#ffb020" : k ? "#e11d48" : "#2f80ed");
  const pin = $derived(v ? "#e9dcc0" : k ? "#8f7ba8" : "#d9d9e3");

  function poke() {
    squish = false; requestAnimationFrame(() => (squish = true));
    onpoke?.();
  }
</script>

<button type="button" class="pichan {squish ? 'squish' : ''}" style="width:{size}px;height:{size}px" onclick={poke}
  onanimationend={() => (squish = false)} aria-label={v ? "The dragon mascot. Tap to hear a quip." : "Pi-chan, the mascot. Tap to hear what she thinks."}>
  <svg viewBox="0 0 120 120" width={size} height={size} aria-hidden="true">
    {#if v}
      <!-- dragon: wings and a curled tail behind the body -->
      <g class="wings" stroke={ink} stroke-width="2.5" stroke-linejoin="round">
        <g class="wing-l"><path d="M24 52 L3 18 L10 34 L0 40 L10 48 L2 58 L14 60 L24 70 Z" fill="#1f7466" />
          <path d="M22 54 L8 28 M21 60 L6 46" stroke="#7fe0c4" stroke-width="1.6" opacity=".7" /></g>
        <g class="wing-r"><path d="M96 52 L117 18 L110 34 L120 40 L110 48 L118 58 L106 60 L96 70 Z" fill="#1f7466" />
          <path d="M98 54 L112 28 M99 60 L114 46" stroke="#7fe0c4" stroke-width="1.6" opacity=".7" /></g>
      </g>
      <path d="M88 96 Q112 104 113 86 Q114 76 104 78" fill="none" stroke={ink} stroke-width="9" stroke-linecap="round" />
      <path d="M88 96 Q112 104 113 86 Q114 76 104 78" fill="none" stroke={body} stroke-width="5" stroke-linecap="round" />
      <path d="M104 78 L96 70 L108 72 Z" fill="#ff7a1a" stroke={ink} stroke-width="2" stroke-linejoin="round" />
      <!-- claws -->
      <g fill={pin} stroke={ink} stroke-width="2.2">
        <path d="M36 96 h12 v8 l-3 6 -3 -5 -3 5 -3 -6 Z" /><path d="M72 96 h12 v8 l-3 6 -3 -5 -3 5 -3 -6 Z" />
      </g>
    {:else}
    <!-- pins: arms & feet -->
    <g fill={pin} stroke={ink} stroke-width="2.5">
      <rect x="8" y="46" width="14" height="7" rx="3" /><rect x="8" y="60" width="14" height="7" rx="3" />
      <rect x="98" y="46" width="14" height="7" rx="3" /><rect x="98" y="60" width="14" height="7" rx="3" />
      <rect x="38" y="96" width="8" height="14" rx="3" /><rect x="56" y="96" width="8" height="14" rx="3" /><rect x="74" y="96" width="8" height="14" rx="3" />
    </g>
    {/if}

    {#if k}
      <!-- cat ears -->
      <g stroke={ink} stroke-width="3" stroke-linejoin="round">
        <path d="M26 34 L30 6 L52 26 Z" fill={body} /><path d="M94 34 L90 6 L68 26 Z" fill={body} />
        <path d="M31 27 L33 14 L44 25 Z" fill="#a259ff" stroke="none" /><path d="M89 27 L87 14 L76 25 Z" fill="#a259ff" stroke="none" />
      </g>
    {/if}

    <!-- body -->
    <rect x="20" y="22" width="80" height="78" rx="20" fill={body} stroke={ink} stroke-width="3.5" />
    <path d="M30 32 Q60 24 90 32" fill="none" stroke={bodyHi} stroke-width="5" stroke-linecap="round" opacity=".8" />
    <circle cx="31" cy="90" r="2.5" fill={ink} opacity=".5" />

    {#if v}
      <!-- belly scales -->
      <g fill="none" stroke="#1f7466" stroke-width="2" opacity=".75">
        <path d="M46 94 q7 -6 14 0 q7 -6 14 0" /><path d="M50 88 q5 -4 10 0 q5 -4 10 0" />
      </g>
      <!-- horned helmet with a nose guard -->
      <g stroke={ink} stroke-width="2.6" stroke-linejoin="round">
        <path d="M30 26 Q22 16 14 2 Q30 8 40 22 Z" fill="#f3e6c4" /><path d="M90 26 Q98 16 106 2 Q90 8 80 22 Z" fill="#f3e6c4" />
        <path d="M17 6 Q24 12 27 18 M103 6 Q96 12 93 18" fill="none" stroke="#c9b48a" stroke-width="2" />
        <path d="M24 34 Q24 6 60 6 Q96 6 96 34 Z" fill="#9aa7ae" />
        <path d="M44 12 Q60 6 76 12" fill="none" stroke="#d6dee2" stroke-width="3" stroke-linecap="round" />
        <rect x="22" y="28" width="76" height="9" rx="3" fill="#c8913a" />
        <path d="M56 36 h8 v12 l-4 4 -4 -4 Z" fill="#9aa7ae" />
      </g>
      <g fill="#fff3d0"><circle cx="30" cy="32.5" r="1.8" /><circle cx="45" cy="32.5" r="1.8" /><circle cx="75" cy="32.5" r="1.8" /><circle cx="90" cy="32.5" r="1.8" /></g>
    {:else if !k}
      <!-- bow -->
      <g transform="translate(86 24) rotate(18)" stroke={ink} stroke-width="2.5" stroke-linejoin="round">
        <path d="M0 0 L-16 -10 L-16 10 Z" fill="#ff4fa3" /><path d="M0 0 L16 -10 L16 10 Z" fill="#ff4fa3" />
        <circle r="4.5" fill="#ff8fc6" />
      </g>
    {/if}

    <!-- eyes -->
    <g class="eyes">
      {#if mood === "happy"}
        <path d="M34 58 Q42 48 50 58" fill="none" stroke={ink} stroke-width="4" stroke-linecap="round" />
        <path d="M70 58 Q78 48 86 58" fill="none" stroke={ink} stroke-width="4" stroke-linecap="round" />
      {:else if mood === "dizzy"}
        <path d="M42 56 m-7 0 a7 7 0 1 0 7 -7 a4.5 4.5 0 1 0 -4.5 4.5 a2 2 0 1 0 2 -2" fill="none" stroke={ink} stroke-width="2.8" stroke-linecap="round" />
        <path d="M78 56 m-7 0 a7 7 0 1 0 7 -7 a4.5 4.5 0 1 0 -4.5 4.5 a2 2 0 1 0 2 -2" fill="none" stroke={ink} stroke-width="2.8" stroke-linecap="round" />
      {:else}
        {#each [42, 78] as cx}
          <ellipse {cx} cy="57" rx="9.5" ry={mood === "angry" ? 7 : 12} fill="#fff" stroke={ink} stroke-width="2.5" />
          <ellipse {cx} cy={mood === "angry" ? 58 : 59} rx="6.5" ry={mood === "angry" ? 5.5 : 8.5} fill={iris} />
          <ellipse {cx} cy={mood === "angry" ? 58 : 60} rx={v ? 1.6 : 3.4} ry={mood === "angry" ? (v ? 4.5 : 3) : v ? 7 : 4.6} fill={ink} />
          <circle cx={cx + 2.6} cy={mood === "angry" ? 55.5 : 54} r="2.6" fill="#fff" />
          <circle cx={cx - 2.6} cy={mood === "angry" ? 60 : 63} r="1.3" fill="#fff" />
        {/each}
        {#if mood === "angry"}
          <path d="M31 45 L51 50" stroke={ink} stroke-width="3.5" stroke-linecap="round" />
          <path d="M89 45 L69 50" stroke={ink} stroke-width="3.5" stroke-linecap="round" />
        {:else if mood === "worried"}
          <path d="M33 46 Q42 40 50 44" fill="none" stroke={ink} stroke-width="3" stroke-linecap="round" transform="rotate(-10 42 44)" />
          <path d="M87 46 Q78 40 70 44" fill="none" stroke={ink} stroke-width="3" stroke-linecap="round" transform="rotate(10 78 44)" />
        {/if}
      {/if}
    </g>

    <!-- blush -->
    <g fill={v ? "#ff8a3d" : "#ff5d9e"} opacity={k ? 0.55 : v ? 0.5 : 0.7}>
      <ellipse cx="32" cy="74" rx="7" ry="4" /><ellipse cx="88" cy="74" rx="7" ry="4" />
    </g>
    <g stroke="#ff2f86" stroke-width="1.5" stroke-linecap="round" opacity=".8">
      <path d="M28 72l-2 4M32 72l-2 4M36 72l-2 4" /><path d="M84 72l-2 4M88 72l-2 4M92 72l-2 4" />
    </g>

    {#if v}
      <g fill={ink}><ellipse cx="55" cy="69" rx="1.6" ry="1.1" /><ellipse cx="65" cy="69" rx="1.6" ry="1.1" /></g>
      {#if mood === "angry" || mood === "worried"}
        <g class="smoke" fill="#c7d0d4" stroke={ink} stroke-width="1.6" opacity=".9">
          <circle cx="50" cy="62" r="3.5" /><circle cx="46" cy="56" r="2.5" /><circle cx="70" cy="62" r="3.5" /><circle cx="74" cy="56" r="2.5" />
        </g>
      {/if}
    {/if}
    <!-- mouth -->
    {#if mood === "happy"}
      <path d="M52 73 Q60 84 68 73 Z" fill="#c2185b" stroke={ink} stroke-width="2.5" stroke-linejoin="round" />
    {:else if mood === "angry"}
      <path d="M53 79 Q60 73 67 79" fill="none" stroke={ink} stroke-width="3" stroke-linecap="round" />
      <!-- anger mark -->
      <g transform="translate(96 30)" stroke="#e53935" stroke-width="3" stroke-linecap="round" fill="none">
        <path d="M-6 -2 Q-2 -2 -2 -6M2 -6 Q2 -2 6 -2M6 2 Q2 2 2 6M-2 6 Q-2 2 -6 2" />
      </g>
    {:else if mood === "worried"}
      <path d="M53 78 Q57 74 60 78 Q63 82 67 78" fill="none" stroke={ink} stroke-width="2.8" stroke-linecap="round" />
      <path d="M95 38 Q99 46 95 50 Q91 46 95 38 Z" fill="#7cc4ff" stroke={ink} stroke-width="2" />
    {:else if mood === "dizzy"}
      <path d="M50 78 Q54 74 58 78 Q62 82 66 78 Q68 76 70 78" fill="none" stroke={ink} stroke-width="2.8" stroke-linecap="round" />
    {:else}
      <path d="M55 75 Q60 80 65 75" fill="none" stroke={ink} stroke-width="3" stroke-linecap="round" />
    {/if}
    {#if v && (mood === "normal" || mood === "happy")}
      <path d="M57 76.5 l1.8 4 1.8 -4 Z" fill="#fff" stroke={ink} stroke-width="1.2" stroke-linejoin="round" />
    {/if}
    {#if v && mood === "angry"}
      <!-- a little burst of dragonfire -->
      <g transform="translate(60 80)"><g class="fire">
        <path d="M0 0 Q-10 10 -4 24 Q0 16 4 24 Q10 10 0 0 Z" fill="#ff7a1a" stroke={ink} stroke-width="2" />
        <path d="M0 6 Q-4 12 -1 19 Q0 15 2 19 Q4 12 0 6 Z" fill="#ffd36a" />
      </g></g>
    {/if}
  </svg>
</button>

<style>
  .pichan { display: block; flex: none; padding: 0; border: 0; background: none; cursor: pointer; animation: bob 2.6s ease-in-out infinite; transform-origin: 50% 100%; }
  .pichan:focus-visible { outline: 3px dashed var(--c-brand); outline-offset: 4px; border-radius: 24px; }
  .pichan.squish { animation: squish .45s cubic-bezier(.3,1.6,.5,1); }
  .eyes { transform-origin: 60px 57px; animation: blink 4.2s infinite; }
  @keyframes bob { 0%, 100% { transform: translateY(0) rotate(-2deg); } 50% { transform: translateY(-5px) rotate(2deg); } }
  @keyframes squish { 0% { transform: scale(1); } 30% { transform: scale(1.18, .82); } 60% { transform: scale(.92, 1.1); } 100% { transform: scale(1); } }
  @keyframes blink { 0%, 94%, 100% { transform: scaleY(1); } 96% { transform: scaleY(.08); } }
  .wing-l { transform-origin: 24px 60px; animation: flap-l 1.6s ease-in-out infinite; }
  .wing-r { transform-origin: 96px 60px; animation: flap-r 1.6s ease-in-out infinite; }
  @keyframes flap-l { 0%, 100% { transform: rotate(0); } 50% { transform: rotate(-14deg); } }
  @keyframes flap-r { 0%, 100% { transform: rotate(0); } 50% { transform: rotate(14deg); } }
  .smoke { animation: puff 1.4s ease-out infinite; }
  @keyframes puff { from { transform: translateY(2px); opacity: .9; } to { transform: translateY(-6px); opacity: 0; } }
  .fire { transform-origin: 0 0; animation: flick .18s steps(2) infinite; }
  @keyframes flick { 50% { transform: scale(1.1, .92); } }
  @media (prefers-reduced-motion: reduce) { .pichan, .eyes, .wing-l, .wing-r, .smoke, .fire { animation: none; } }
</style>
