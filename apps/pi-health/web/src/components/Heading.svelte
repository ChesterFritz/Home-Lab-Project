<script>
  import { store } from "../lib/store.svelte.js";
  import { COPY } from "../lib/anime.js";
  let { key, id, fallback } = $props();
  const h = $derived(store.anime ? COPY[store.anime].heads[key] : [fallback, null]);
</script>

<h2 {id} class="heading flex items-baseline gap-2 text-[17px] font-semibold">{h[0]}{#if h[1]}<span class="jp">{h[1]}</span>{/if}</h2>
