<script>
  import { store } from "../lib/store.svelte.js";
  const info = $derived(store.state?.info ?? {});
  const rows = $derived([["Board", info.model], ["System", info.os], ["Kernel", info.kernel],
    ["CPU", info.cores ? `${info.cores} × Cortex-A7, up to ${info.cpu_max_mhz} MHz` : null], ["GPU", info.gpu_name]].filter((r) => r[1]));
</script>

<section class="text-[12.5px] text-ink-3">
  <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
    {#each rows as [k, v]}<dt>{k}</dt><dd class="text-ink-2">{v}</dd>{/each}
  </dl>
  <p class="mt-3 max-w-[68ch]">Power is an estimate. The Orange Pi PC has no current sensor, so watts are worked out from CPU load, clock speed, core voltage and GPU activity. For exact numbers, use a USB power meter on the supply.</p>
</section>
