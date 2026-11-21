<script>
  // "Where the money went", built for a phone: the flow diagram unrolled into rows that read
  // top to bottom: what came in, where it went, what was left. Every bar shares one scale
  // (the bigger of in and out), so lengths compare across sections. Rows are direct-labeled,
  // so no tooltip is needed; tapping a category opens its transactions.
  import { animate, stagger } from "motion";
  import { peso } from "../lib/fmt.js";
  import { reduced } from "../lib/motion.js";

  let { summary, onpick } = $props();
  let root = $state();
  const MAX_OUT = 6;

  const scale = $derived(Math.max(summary.income, summary.expense, 1));
  const ins = $derived(summary.income_by_category);
  const outs = $derived.by(() => {
    const list = summary.expense_by_category;
    if (list.length <= MAX_OUT) return list;
    const rest = list.slice(MAX_OUT - 1);
    return [
      ...list.slice(0, MAX_OUT - 1),
      { id: null, name: `${rest.length} more categories`, amount: rest.reduce((s, c) => s + c.amount, 0), folded: true },
    ];
  });
  const pct = (v) => `${Math.max(1.5, (v / scale) * 100)}%`;
  const share = (v) => (summary.expense > 0 ? Math.round((v / summary.expense) * 100) : 0);

  // Bars grow in, in reading order, whenever the month changes.
  let grown = null;
  $effect(() => {
    if (!root || reduced() || grown === summary) return;
    grown = summary;
    const bars = root.querySelectorAll("[data-bar]");
    const a = animate(bars, { scaleX: [0, 1] }, { duration: 0.55, delay: stagger(0.035), ease: [0.22, 1, 0.36, 1] });
    return () => a.complete();
  });
</script>

{#snippet row(name, amount, color, opts = {})}
  {#snippet inner()}
    <span class="flex items-baseline justify-between gap-3">
      <span class="min-w-0 truncate font-semibold">{name}</span>
      <span class="num shrink-0 font-bold">{peso(amount)}{#if opts.share != null}<span class="ml-1.5 text-[12px] font-semibold text-muted">{opts.share}%</span>{/if}</span>
    </span>
    <span class="mt-1.5 block h-2.5 rounded-full bg-inset">
      <span data-bar class="block h-full origin-left rounded-full" style="width:{pct(amount)}; background:{color}"></span>
    </span>
  {/snippet}
  {#if opts.onclick}
    <button class="block w-full rounded-xl px-1 py-2 text-left active:bg-inset" onclick={opts.onclick}>{@render inner()}</button>
  {:else}
    <div class="px-1 py-2">{@render inner()}</div>
  {/if}
{/snippet}

<div bind:this={root}>
  <h3 class="mb-1 text-[13px] font-bold text-muted">Came in, {peso(summary.income)}</h3>
  {#each ins as c (c.id)}
    {@render row(c.name, c.amount, "var(--in)")}
  {:else}
    <p class="py-2 text-ink-2">Nothing came in.</p>
  {/each}
  {#if summary.net < 0}
    {@render row("Taken from your balances", -summary.net, "var(--line-strong)")}
  {/if}

  <h3 class="mb-1 mt-4 text-[13px] font-bold text-muted">Went out, {peso(summary.expense)}</h3>
  {#each outs as c (c.name)}
    {@render row(c.name, c.amount, "var(--out)", { share: share(c.amount), onclick: c.folded ? undefined : () => onpick?.(c) })}
  {:else}
    <p class="py-2 text-ink-2">Nothing went out.</p>
  {/each}

  {#if summary.net > 0}
    <div class="mt-3 border-t border-line pt-2">
      {@render row("Left over", summary.net, "var(--in)")}
    </div>
  {/if}
</div>
