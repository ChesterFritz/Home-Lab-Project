<script>
  import { store } from "../lib/store.svelte.js";
  import { ago, dur, fullTime } from "../lib/format.js";
  import SevIcon from "./SevIcon.svelte";
  import Heading from "./Heading.svelte";
  const events = $derived(store.state?.events ?? []);
</script>

<section aria-labelledby="ev-h">
  <div class="mb-3"><Heading key="alerts" id="ev-h" fallback="Alert history" /></div>
  <ul class="card max-h-[520px] divide-y divide-line overflow-auto px-4">
    {#each events as e, i (e.t + ":" + i)}
      {@const done = e.kind === "resolved"}
      <li class="flex items-start gap-3 py-3">
        <span class="pt-0.5"><SevIcon sev={done ? "good" : e.severity} size={20} /></span>
        <div class="min-w-0 flex-1">
          <div class="text-[14.5px] {done || e.severity === 'info' ? 'font-normal' : 'font-semibold'}">{e.title}{done ? ", resolved" : ""}</div>
          {#if done}<div class="text-[12.5px] text-ink-3">Lasted {dur(e.duration, true)}</div>
          {:else if e.detail}<div class="text-[12.5px] text-ink-3">{e.detail}</div>{/if}
        </div>
        <time class="shrink-0 text-[12.5px] text-ink-3" title={fullTime(e.t)}>{ago(e.t, store.now)}</time>
      </li>
    {:else}
      <li class="py-4 text-[14px] text-ink-3">Nothing has gone wrong yet. Alerts and when they cleared will show up here.</li>
    {/each}
  </ul>
</section>
