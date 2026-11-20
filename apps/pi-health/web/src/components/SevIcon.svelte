<script>
  import Icon from "./Icon.svelte";
  let { sev = "good", size = 20 } = $props();
  const bg = { good: "bg-good text-white", warning: "bg-warning text-[#3b2900]", serious: "bg-serious text-white",
               critical: "bg-critical text-white", info: "bg-well text-ink-2 ring-1 ring-line", offline: "bg-ink-3 text-white" };
  const icon = { good: "check", info: "info", offline: "off" };
</script>

<span class="grid shrink-0 place-items-center rounded-full {bg[sev] ?? bg.info}" style="width:{size}px;height:{size}px">
  <Icon name={icon[sev] ?? "alert"} size={Math.round(size * 0.68)} stroke={2.6} />
</span>
