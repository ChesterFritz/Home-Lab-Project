<script>
  // Chuunibyou night: crimson/violet nebula, faint stars, a giant slowly turning magic circle,
  // embers rising from below, and a heavy vignette.
  import MagicCircle from "./MagicCircle.svelte";
  const rnd = (i, k) => ((Math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1 + 1) % 1;
  const embers = Array.from({ length: 26 }, (_, i) => ({
    x: rnd(i, 1) * 100, s: 2 + rnd(i, 2) * 3.5, d: 7 + rnd(i, 3) * 9, delay: -rnd(i, 4) * 16, dx: (rnd(i, 5) - 0.5) * 18 + "vw",
    c: i % 3 ? "#ff3b5c" : "#e8c46a",
  }));
  const stars = Array.from({ length: 40 }, (_, i) => ({ x: rnd(i, 6) * 100, y: rnd(i, 7) * 100, s: 1 + rnd(i, 8) * 1.6, o: 0.2 + rnd(i, 9) * 0.5 }));
</script>

<div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" style="background:
  radial-gradient(ellipse 60% 50% at 15% 85%, rgb(212 42 72 / .28), transparent 70%),
  radial-gradient(ellipse 50% 45% at 85% 15%, rgb(110 40 200 / .3), transparent 70%),
  #07040c" aria-hidden="true">
  {#each stars as st}
    <span class="absolute rounded-full bg-white" style="left:{st.x}%; top:{st.y}%; width:{st.s}px; height:{st.s}px; opacity:{st.o}"></span>
  {/each}
  <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style="opacity:.16; filter: drop-shadow(0 0 6px #d42a48)">
    <MagicCircle size={Math.max(innerWidth, innerHeight) * 0.95} uid="sky" />
  </div>
  {#each embers as e}
    <span class="ember absolute bottom-[-10px] rounded-full" style="left:{e.x}%; width:{e.s}px; height:{e.s}px; background:{e.c}; box-shadow: 0 0 8px 2px {e.c}; --dx:{e.dx}; animation: ember {e.d}s ease-in {e.delay}s infinite"></span>
  {/each}
  <div class="absolute inset-0" style="background: radial-gradient(ellipse at center, transparent 45%, rgb(0 0 0 / .75) 100%)"></div>
</div>
