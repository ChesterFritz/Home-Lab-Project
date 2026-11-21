<script>
  import { app } from "../lib/store.svelte.js";
  import ChuuniSky from "./ChuuniSky.svelte";
  import MangaPaper from "./MangaPaper.svelte";
  // The color field behind the glass. Its palette follows the time of day (morning, day,
  // evening, night) and the light/dark theme; the blobs drift slowly (still under reduced motion).
  const palettes = {
    morning: { light: ["#ffd6a8", "#a8d8ff", "#ffc2d4", "#c9f2dc"], dark: ["#6b3a1e", "#1d3f6e", "#5a2440", "#1f4a3a"] },
    day: { light: ["#9cc8ff", "#a6f0d6", "#d4c6ff", "#ffe4a6"], dark: ["#1b3d78", "#145a4a", "#3b2f74", "#5b4718"] },
    evening: { light: ["#ffb39c", "#d9a8ff", "#ffd59a", "#9fc0ff"], dark: ["#6e2a2a", "#4a2678", "#6b4a16", "#1e3a74"] },
    night: { light: ["#b9c4ff", "#a3dff2", "#d8c2ff", "#c4d4ff"], dark: ["#1a2a6e", "#0f4a5c", "#3a1f6e", "#14305e"] },
  };
  const period = (h) => (h >= 5 && h < 11 ? "morning" : h >= 11 && h < 17 ? "day" : h >= 17 && h < 20 ? "evening" : "night");

  let now = $state(new Date());
  $effect(() => {
    const t = setInterval(() => (now = new Date()), 5 * 60 * 1000);
    return () => clearInterval(t);
  });

  let dark = $state(false);
  $effect(() => {
    const read = () => {
      const forced = document.documentElement.dataset.theme;
      dark = forced ? forced === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    };
    read();
    const mq = matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", read);
    const mo = new MutationObserver(read);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => (mq.removeEventListener("change", read), mo.disconnect());
  });

  const colors = $derived(palettes[period(now.getHours())][dark ? "dark" : "light"]);
  const blobs = [
    { x: "-10%", y: "-15%", s: "62vmax", d: "38s" },
    { x: "55%", y: "-20%", s: "55vmax", d: "46s" },
    { x: "60%", y: "45%", s: "60vmax", d: "52s" },
    { x: "-15%", y: "50%", s: "50vmax", d: "42s" },
  ];
</script>

{#if app.anime === "chuuni"}
  <ChuuniSky />
{:else if app.anime === "manga"}
  <MangaPaper />
{:else}
<div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-paper" aria-hidden="true">
  {#each blobs as b, i}
    <div
      class="absolute rounded-full transition-[background] duration-[3000ms]"
      style="left:{b.x}; top:{b.y}; width:{b.s}; height:{b.s}; background: radial-gradient(circle at center, {colors[i]} 0%, transparent 68%);
             opacity:{dark ? 0.85 : 0.9}; filter: blur(40px); animation: drift {b.d} ease-in-out {i * -7}s infinite alternate;"
    ></div>
  {/each}
</div>
{/if}
