<script>
  import { onMount } from "svelte";
  import { store } from "./lib/store.svelte.js";
  import Header from "./components/Header.svelte";
  import StatusCard from "./components/StatusCard.svelte";
  import Vitals from "./components/Vitals.svelte";
  import Apps from "./components/Apps.svelte";
  import Charts from "./components/Charts.svelte";
  import Services from "./components/Services.svelte";
  import Events from "./components/Events.svelte";
  import SystemInfo from "./components/SystemInfo.svelte";
  import BottomNav from "./components/BottomNav.svelte";
  import Ticker from "./components/anime/Ticker.svelte";
  import AnimeLayer from "./components/anime/AnimeLayer.svelte";

  onMount(() => store.start());
  // Japanese display fonts are big; fetch them only once an anime theme is in use.
  $effect(() => { if (store.anime) import("./lib/animeFonts.js"); });
  $effect(() => {
    const n = store.state?.alerts?.length ?? 0;
    document.title = (n ? `(${n}) ` : "") + "Pi Health";
  });
  // On phones only the active tab shows; from lg up everything is visible.
  const show = (tab) => (store.tab === tab ? "" : "max-lg:hidden");
</script>

<Header />
{#if store.anime}
  {#key store.anime}<Ticker /><AnimeLayer />{/key}
{/if}

<main class="relative z-10 mx-auto max-w-[1240px] px-4 pt-4 pb-[calc(88px+env(safe-area-inset-bottom))] lg:grid lg:grid-cols-[minmax(0,1fr)_380px] lg:gap-6 lg:pb-12">
  <div class="min-w-0 space-y-6">
    <div class="space-y-3 {show('overview')}">
      <StatusCard />
      <Vitals />
    </div>
    <div class={show("charts")}><Charts /></div>
  </div>

  <aside class="min-w-0 space-y-6 max-lg:mt-6 max-lg:first:mt-0">
    <div class={show("overview")}><Apps /></div>
    <div class={show("services")}><Services /></div>
    <div class={show("alerts")}><Events /></div>
    <div class="max-lg:hidden"><SystemInfo /></div>
    <div class="lg:hidden {show('services')}"><SystemInfo /></div>
  </aside>
</main>

<BottomNav />
