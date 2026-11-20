<script>
  import { store } from "../lib/store.svelte.js";
  import Icon from "./Icon.svelte";
  import { COPY } from "../lib/anime.js";
  const alerts = $derived(store.state?.alerts ?? []);
  const sevBg = { critical: "bg-critical", serious: "bg-serious", warning: "bg-warning text-[#3b2900]" };
  const tabs = [
    { id: "overview", label: "Overview", icon: "home" },
    { id: "charts", label: "Charts", icon: "chart" },
    { id: "services", label: "Services", icon: "server" },
    { id: "alerts", label: "Alerts", icon: "bell" },
  ];
</script>

<nav class="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-panel/90 backdrop-blur-md lg:hidden"
  style="padding-bottom: env(safe-area-inset-bottom)" aria-label="Sections">
  <div class="mx-auto grid max-w-md grid-cols-4">
    {#each tabs as t}
      {@const on = store.tab === t.id}
      <button type="button" onclick={() => store.setTab(t.id)} aria-current={on ? "page" : undefined}
        class="relative flex flex-col items-center gap-0.5 pt-2.5 pb-2 text-[11.5px] font-medium transition {on ? 'text-ink' : 'text-ink-3'}">
        {#if on}<span class="absolute top-0 h-[3px] w-8 rounded-b-full bg-brand"></span>{/if}
        <span class="relative">
          <Icon name={t.icon} size={22} stroke={on ? 2.1 : 1.8} />
          {#if t.id === "alerts" && alerts.length}
            <span class="absolute -top-1.5 -right-2.5 grid min-w-4 place-items-center rounded-full px-1 text-[10px] leading-4 font-bold text-white {sevBg[alerts[0].severity] ?? 'bg-critical'}">{alerts.length}</span>
          {/if}
        </span>
        {store.anime ? COPY[store.anime].tabs[t.id] : t.label}
      </button>
    {/each}
  </div>
</nav>
