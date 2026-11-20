<script>
  import { store } from "../lib/store.svelte.js";
  import { dur } from "../lib/format.js";
  import Icon from "./Icon.svelte";
  import ThemeMenu from "./ThemeMenu.svelte";
  import { COPY } from "../lib/anime.js";
  const info = $derived(store.state?.info ?? {});
</script>

<header class="sticky top-0 z-20 border-b border-line/70 bg-page/85 backdrop-blur-md supports-[backdrop-filter]:bg-page/70"
  style="padding-top: env(safe-area-inset-top)">
  <div class="mx-auto flex h-14 max-w-[1240px] items-center gap-3 px-4">
    <img src="icon.svg" alt="" class="size-8 rounded-[9px]" />
    <div class="min-w-0 leading-tight">
      <div class="truncate text-[15px] font-semibold">{info.hostname ?? "Orange Pi"}</div>
      {#if store.anime}
        <div class="brand-jp truncate text-[11.5px]">{COPY[store.anime].brand}</div>
      {:else}
        <div class="hidden truncate text-[12.5px] text-ink-3 sm:block">{info.model ?? ""}</div>
      {/if}
    </div>
    <div class="flex-1"></div>
    <span class="flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-[12.5px] text-ink-2" role="status">
      {#if store.status === "live"}
        <span class="relative flex size-2"><span class="absolute inline-flex size-full animate-ping rounded-full bg-good opacity-50"></span><span class="relative inline-flex size-2 rounded-full bg-good"></span></span>Live
      {:else if store.status === "offline"}
        <span class="size-2 rounded-full bg-critical"></span>Offline{store.lastOk ? ` ${dur((Date.now() - store.lastOk) / 1000)}` : ""}
      {:else}
        <span class="size-2 rounded-full bg-ink-3"></span>Connecting
      {/if}
    </span>
    <ThemeMenu />
  </div>
</header>
