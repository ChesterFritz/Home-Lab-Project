<script>
  import { store } from "../lib/store.svelte.js";
  import { ago, bytes } from "../lib/format.js";
  import SevIcon from "./SevIcon.svelte";
  import Heading from "./Heading.svelte";

  const LEVEL = { good: "OK", warning: "Warning", serious: "Serious", critical: "Critical" };
  const INK = { good: "text-good-ink", warning: "text-warning-ink", serious: "text-serious-ink", critical: "text-critical-ink" };
  const rows = $derived.by(() => {
    const c = store.state?.checks ?? {}, now = store.now, out = [];
    const keys = new Set((store.state?.alerts ?? []).map((a) => a.key));
    for (const ct of c.containers ?? []) {
      const sev = ct.state !== "running" ? "critical" : ct.health === "unhealthy" ? "serious" : "good";
      out.push([sev, ct.name, ct.image, ct.status.replace(/\s*\((healthy|unhealthy|health: starting)\)/, "")]);
    }
    if (c.docker_error) out.push(["critical", "Docker", c.docker_error, "Not responding"]);
    if (c.dns) out.push([c.dns.ok ? "good" : "critical", "AdGuard DNS", "Answering on this Pi, port 53", c.dns.ok ? `${c.dns.ms} ms` : "No answer"]);
    if (c.internet) out.push([c.internet.ok ? "good" : "serious", "Internet", "Reaching 1.1.1.1 and 8.8.8.8", c.internet.ok ? `${c.internet.ms} ms` : "Unreachable"]);
    if (c.vpn_up != null) out.push([c.vpn_up ? "good" : "serious", "Tailscale", "Remote access and exit node", c.vpn_up ? "Connected" : "Down"]);
    if (c.failed_units) out.push([c.failed_units.length ? "warning" : "good", "System services", c.failed_units.length ? c.failed_units.join(", ") : "None have failed", c.failed_units.length ? `${c.failed_units.length} failed` : "All running"]);
    if (c.t) { const b = c.backup; out.push([keys.has("backup") ? "warning" : "good", "Nightly backup", b ? `${bytes(b.size)}, kept 14 days` : "No backups found", b ? ago(b.mtime, now) : "Missing"]); }
    return out;
  });
  const checked = $derived(store.state?.checks?.t);
</script>

<section aria-labelledby="svc-h">
  <div class="mb-3 flex items-baseline gap-3">
    <Heading key="services" id="svc-h" fallback="Services" />
    {#if checked}<span class="text-[12.5px] text-ink-3">Checked {ago(checked, store.now)}</span>{/if}
  </div>
  <ul class="card divide-y divide-line px-4">
    {#each rows as [sev, name, sub, right] (name)}
      <li class="flex items-center gap-3 py-3">
        <SevIcon {sev} size={20} />
        <div class="min-w-0 flex-1">
          <div class="truncate text-[14.5px] font-medium">{name}</div>
          <div class="truncate text-[12.5px] text-ink-3">{sub}</div>
        </div>
        <div class="shrink-0 text-right text-[12.5px] leading-tight">
          <div class="font-semibold {INK[sev]}">{LEVEL[sev]}</div>
          <div class="text-ink-2">{right}</div>
        </div>
      </li>
    {:else}
      <li class="py-4 text-[14px] text-ink-3">Running the first checks.</li>
    {/each}
  </ul>
</section>
