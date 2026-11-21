<script>
  // Piso, an original coin spirit with cat ears. Bobs, blinks, talks when tapped, hops when you
  // save. In the chuunibyou style it becomes the Dark Coin Lord: eyepatch, glowing crimson eye,
  // smirk and cape. In the manga style it's inked in black and white. `face` = small and still.
  import { app } from "../lib/store.svelte.js";
  import { peso } from "../lib/fmt.js";
  import { reduced } from "../lib/motion.js";

  let { size = 64, face = false, bubble = "right" } = $props();
  const lord = $derived(app.anime === "chuuni");

  const lines = {
    chuuni: [
      "Kukuku… my Evil Eye sees your spending.",
      "The seal on your savings holds. For now.",
      "Do not underestimate the Dark Coin Lord!",
      "This right hand… craves a budget.",
      "Every peso is a pact. Honor it.",
      "The Abyss whispers: skip the milk tea.",
    ],
    manga: ["Every peso counts!", "Logged it? Future you says thanks!", "Saving a little is still saving.", "Payday arc, let's go!", "Plot twist: you stayed on budget."],
  };
  const cheers = { chuuni: ["The pact is sealed.", "Inscribed in the Chronicle!", "Kukuku… recorded."], manga: ["Logged! ✦", "Nice one!", "Got it, saved!"] };

  let say = $state("");
  let hopping = $state(false);
  let timer;

  function talk(text) {
    say = text;
    clearTimeout(timer);
    timer = setTimeout(() => (say = ""), 3400);
    if (reduced()) return;
    hopping = false;
    requestAnimationFrame(() => (hopping = true));
  }
  function poke() {
    const pool = lines[lord ? "chuuni" : "manga"].filter((l) => l !== say);
    if (app.meta) pool.push(lord ? `Behold! ${peso(app.meta.netWorth)} of sealed power!` : `Net worth: ${peso(app.meta.netWorth)}!`);
    talk(pool[Math.floor(Math.random() * pool.length)]);
  }

  let seen = app.version;
  $effect(() => {
    if (face || app.version === seen) return;
    seen = app.version;
    const c = cheers[lord ? "chuuni" : "manga"];
    talk(c[app.version % c.length]);
  });

  const ink = "#2a1430";
</script>

{#snippet coin()}
  <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true" class="mascot overflow-visible" style={lord ? "filter: drop-shadow(0 0 6px rgb(212 42 72 / .6))" : ""}>
    {#if lord}
      <!-- cape -->
      <path d="M8 40 Q4 58 14 62 L32 56 L50 62 Q60 58 56 40 Q46 52 32 52 Q18 52 8 40 Z" fill="#5a0f22" stroke={ink} stroke-width="2" />
      <path d="M12 44 Q20 54 32 54 Q44 54 52 44" fill="none" stroke="#d42a48" stroke-width="1.2" />
    {/if}
    <g style="transform-origin: 18px 18px; animation: {hopping ? 'ear-wiggle .6s ease' : 'none'}">
      <path d={lord ? "M10 23 L11 1 L27 14 Z" : "M10 22 L14 4 L27 14 Z"} fill="#ffcf4a" stroke={ink} stroke-width="2.2" stroke-linejoin="round" />
      <path d="M14.5 17 L15.5 8 L22 13.5 Z" fill={lord ? "#d42a48" : "#ff9ec7"} />
    </g>
    <g style="transform-origin: 46px 18px; animation: {hopping ? 'ear-wiggle .6s ease .08s' : 'none'}">
      <path d={lord ? "M54 23 L53 1 L37 14 Z" : "M54 22 L50 4 L37 14 Z"} fill="#ffcf4a" stroke={ink} stroke-width="2.2" stroke-linejoin="round" />
      <path d="M49.5 17 L48.5 8 L42 13.5 Z" fill={lord ? "#d42a48" : "#ff9ec7"} />
    </g>
    <circle cx="32" cy="36" r="24" fill="#f2b628" stroke={ink} stroke-width="2.4" />
    <circle cx="32" cy="36" r="19" fill="#ffd95e" />
    <path d="M20 28 a14 14 0 0 1 9 -9" stroke="#fff6c9" stroke-width="3" stroke-linecap="round" fill="none" />

    {#if lord}
      <!-- brows -->
      <path d="M19 28.5 L29 31" stroke={ink} stroke-width="2.2" stroke-linecap="round" />
      <path d="M45 28.5 L35 31" stroke={ink} stroke-width="2.2" stroke-linecap="round" />
      <!-- the cursed eye: crimson with a slit pupil -->
      <g style="animation: {face ? 'none' : 'pulse-eye 2.4s ease-in-out infinite'}">
        <ellipse cx="39.5" cy="35.5" rx="3.6" ry="4.2" fill="#d42a48" stroke={ink} stroke-width="1.2" />
        <ellipse cx="39.5" cy="35.5" rx="0.9" ry="3.2" fill="#14040a" />
        <circle cx="40.8" cy="33.8" r=".9" fill="#ffd1da" />
      </g>
      <!-- eyepatch and strap -->
      <path d="M9 27 L55 24" stroke={ink} stroke-width="1.8" />
      <path d="M19.5 31 Q24.5 29 29.5 31 L28.5 39 Q24.5 41.5 20.5 39 Z" fill={ink} />
      <!-- smirk -->
      <path d="M27 43.5 Q33 46.5 38 42" stroke={ink} stroke-width="1.8" fill="none" stroke-linecap="round" />
      <path d="M36 42.5 l1.2 2.2 l1 -2.6" fill="#fff" stroke={ink} stroke-width=".8" />
    {:else}
      <g style="transform-origin: 32px 35px; animation: {face ? 'none' : 'blink 4.2s infinite'}">
        <ellipse cx="24.5" cy="35" rx="3.2" ry="4.2" fill={ink} />
        <ellipse cx="39.5" cy="35" rx="3.2" ry="4.2" fill={ink} />
        <circle cx="25.6" cy="33.4" r="1.2" fill="#fff" />
        <circle cx="40.6" cy="33.4" r="1.2" fill="#fff" />
      </g>
      <ellipse cx="19" cy="42" rx="3.6" ry="2.2" fill="#ff8fb8" opacity=".8" />
      <ellipse cx="45" cy="42" rx="3.6" ry="2.2" fill="#ff8fb8" opacity=".8" />
      <path d="M28.5 41.5 q1.75 2.2 3.5 0 q1.75 2.2 3.5 0" stroke={ink} stroke-width="1.8" fill="none" stroke-linecap="round" />
    {/if}
  </svg>
{/snippet}

{#if face}
  {@render coin()}
{:else}
  <div class="relative inline-block">
    <button
      class="block rounded-full"
      style="animation: {hopping ? 'hop .6s cubic-bezier(.34,1.56,.64,1)' : reduced() ? 'none' : 'bob 3s ease-in-out infinite'}"
      onanimationend={(e) => e.animationName === "hop" && (hopping = false)}
      onclick={poke}
      aria-label={lord ? "The Dark Coin Lord. Tap for a decree." : "Piso, the Pitaka mascot. Tap for a message."}
    >
      {@render coin()}
    </button>
    {#if say}
      {#key say}
        <p
          class="absolute z-40 w-max max-w-[200px] px-3 py-2 text-[13px] font-semibold leading-snug
                 {lord ? 'rounded bg-[#14040c] text-[#f6e7c2] ring-1 ring-[#d42a48] shadow-[0_0_24px_-4px_rgb(212_42_72/.8)]' : 'rounded-[18px] bg-white text-black ring-[2.5px] ring-black'}
                 {bubble === 'right' ? 'left-full top-1/2 ml-3 -translate-y-1/2' : 'right-0 top-full mt-2'}"
          style="animation: bubble-in .3s cubic-bezier(.34,1.56,.64,1); {lord ? 'font-family: Cinzel, Georgia, serif; letter-spacing: .02em' : ''}"
          role="status"
        >
          {say}
        </p>
      {/key}
    {/if}
  </div>
{/if}
