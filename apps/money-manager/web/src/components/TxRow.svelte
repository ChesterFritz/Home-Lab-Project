<script>
  // Amounts stay in ink with a +/− sign; the colored marker carries in/out/transfer identity.
  import { peso, splitEmoji } from "../lib/fmt.js";

  let { tx, onclick } = $props();
  const sign = $derived(
    tx.kind === "income" || (tx.kind === "adjust" && tx.direction === "up") || (tx.kind === "transfer" && tx.direction === "in") ? 1
    : tx.kind === "transfer" && tx.direction === "out" ? 0 : -1
  );
  const marker = $derived({ income: "var(--in)", expense: "var(--out)", transfer: "var(--xfer)", adjust: "var(--line-strong)" }[tx.kind]);
  const parts = $derived(
    tx.kind === "transfer"
      ? ["", tx.direction === "in" ? `From ${tx.toAccount || "another account"}` : `To ${tx.toAccount || "another account"}`]
      : tx.kind === "adjust"
        ? ["", "Balance adjustment"]
        : splitEmoji(tx.category)
  );
  const sub = $derived(
    [tx.subcategory, tx.note, tx.kind === "transfer" ? (tx.direction === "in" ? `into ${tx.account}` : `from ${tx.account}`) : tx.account]
      .filter(Boolean)
      .join(", ")
  );
</script>

<button class="flex w-full items-center gap-3 rounded-2xl px-2 py-2.5 text-left hover:bg-inset" {onclick}>
  <span class="h-9 w-1 shrink-0 rounded-full" style="background:{marker}" aria-hidden="true"></span>
  <span class="grid size-10 shrink-0 place-items-center rounded-[13px] bg-inset text-lg font-bold text-ink-2" aria-hidden="true">
    {#if tx.kind === "transfer"}
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h14l-3-3M20 16H6l3 3" /></svg>
    {:else}{parts[0] || parts[1].slice(0, 1)}{/if}
  </span>
  <span class="min-w-0 flex-1">
    <span class="block truncate font-semibold">{parts[1] || "Uncategorized"}</span>
    <span class="block truncate text-sm text-ink-2">{sub}</span>
  </span>
  <span class="num shrink-0 text-right font-semibold">
    {sign === 0 ? peso(tx.amount) : peso(sign * tx.amount, { sign: true })}
    <span class="sr-only">{tx.kind}</span>
  </span>
</button>
