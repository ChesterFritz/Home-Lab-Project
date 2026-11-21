<script>
  // Theme song for the anime themes: the MP3 uploaded to "<flavor>-music", looped quietly.
  // Browsers block sound until the first tap or key press, so it waits for one if needed,
  // and it pauses while the tab is hidden.
  import { store } from "../../lib/store.svelte.js";
  let { flavor } = $props();
  let audio = $state();
  let hidden = $state(document.hidden);
  const src = $derived(store.custom[`${flavor}-music`] ?? null);
  const want = $derived(!!src && store.music && !hidden);

  $effect(() => {
    const vis = () => (hidden = document.hidden);
    document.addEventListener("visibilitychange", vis);
    return () => document.removeEventListener("visibilitychange", vis);
  });

  $effect(() => {
    if (!audio) return;
    if (!want) { audio.pause(); return; }
    audio.volume = 0.35;
    let waiting = false;
    const retry = () => { off(); audio.play().catch(() => {}); };
    const off = () => { if (!waiting) return; waiting = false; removeEventListener("pointerdown", retry); removeEventListener("keydown", retry); };
    audio.play().catch(() => {
      waiting = true;
      addEventListener("pointerdown", retry, { once: true }); addEventListener("keydown", retry, { once: true });
    });
    return off;
  });
</script>

{#if src}<audio bind:this={audio} {src} loop preload="auto"></audio>{/if}
