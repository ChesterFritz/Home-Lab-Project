<script>
  // A glass capsule: previous / month / next, plus a way back to this month.
  import { app } from "../lib/store.svelte.js";
  import { monthName, shiftMonth, ym } from "../lib/fmt.js";
  import { fly } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { reduced } from "../lib/motion.js";
  const now = ym(new Date());
  let dir = $state(1);
  const move = (n) => ((dir = n), (app.month = shiftMonth(app.month, n)));
</script>

<div class="flex items-center gap-2" role="group" aria-label="Month">
  <div class="glass flex items-center rounded-full p-1">
    <button class="grid size-9 place-items-center rounded-full hover:bg-inset" aria-label="Previous month" onclick={() => move(-1)}>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>
    </button>
    <span class="relative grid min-w-[8.5rem] overflow-hidden text-center font-semibold" aria-live="polite">
      {#key app.month}
        <span class="col-start-1 row-start-1" in:fly={{ x: 28 * dir, duration: reduced() ? 0 : 320, easing: cubicOut }} out:fly={{ x: -28 * dir, duration: reduced() ? 0 : 220 }}>{monthName(app.month)}</span>
      {/key}
    </span>
    <button class="grid size-9 place-items-center rounded-full hover:bg-inset disabled:opacity-30" aria-label="Next month" disabled={app.month >= now} onclick={() => move(1)}>
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
    </button>
  </div>
  {#if app.month !== now}
    <button class="glass rounded-full px-3.5 py-2 text-sm font-semibold" onclick={() => ((dir = 1), (app.month = now))}>This month</button>
  {/if}
</div>
