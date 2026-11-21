<script>
  // Frosted, see-through confirmation. The icon carries the tone; the text stays in ink.
  import { fly } from "svelte/transition";
  import { backOut } from "svelte/easing";
  import { app } from "../lib/store.svelte.js";
  import Mascot from "./Mascot.svelte";
</script>

<div class="pointer-events-none fixed inset-x-0 z-[60] flex justify-center px-4" style="top: calc(env(safe-area-inset-top) + 66px)" aria-live="polite">
  {#if app.toast}
    {#key app.toast.id}
      {@const bad = app.toast.tone === "error"}
      <div
        class="glass pointer-events-auto flex items-center gap-2.5 rounded-2xl py-2.5 pl-2.5 pr-4 font-semibold text-ink"
        in:fly|global={{ y: -14, duration: 260, easing: backOut }}
        out:fly|global={{ y: -6, duration: 160 }}
      >
        {#if app.skin === "anime" && !bad}
          <span class="-my-1" aria-hidden="true"><Mascot size={34} face /></span>
        {:else}
        <span class="grid size-7 place-items-center rounded-xl {bad ? 'bg-danger text-white' : 'bg-primary text-on-primary'}" aria-hidden="true">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <path d={bad ? "M12 7v6M12 17h.01" : "M5 12.5l4.5 4.5L19 7.5"} />
          </svg>
        </span>
        {/if}
        {app.toast.text}
      </div>
    {/key}
  {/if}
</div>
