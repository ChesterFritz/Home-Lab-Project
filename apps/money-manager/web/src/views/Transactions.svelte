<script>
  import { flip } from "svelte/animate";
  import { fade, fly, slide } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { reduced } from "../lib/motion.js";
  import { app, openAdd, openEdit } from "../lib/store.svelte.js";
  import { api } from "../lib/api.js";
  import { dayLabel, iso, monthName, monthRange, peso } from "../lib/fmt.js";
  import TxRow from "../components/TxRow.svelte";

  let list = $state([]);
  let loading = $state(true);
  let error = $state("");
  let query = $state("");
  let kind = $state("all");
  let account = $state("");
  const today = iso(new Date());

  $effect(() => {
    const { from, to } = monthRange(app.month);
    app.version;
    let stale = false;
    loading = true;
    api
      .transactions(from, to)
      .then((r) => !stale && ((list = r), (error = "")))
      .catch((e) => !stale && (error = e.message))
      .finally(() => !stale && (loading = false));
    return () => (stale = true);
  });

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    const cat = app.categoryFilter?.id;
    return list.filter(
      (t) =>
        (kind === "all" || t.kind === kind) &&
        (!account || t.accountId === account || t.toAccountId === account) &&
        (!cat || t.categoryId === cat) &&
        (!q || [t.category, t.subcategory, t.note, t.memo, t.account, t.toAccount, String(t.amount)].join(" ").toLowerCase().includes(q))
    );
  });

  const days = $derived.by(() => {
    const map = new Map();
    for (const t of filtered) {
      if (!map.has(t.date)) map.set(t.date, { date: t.date, items: [], in: 0, out: 0 });
      const d = map.get(t.date);
      d.items.push(t);
      if (t.kind === "income") d.in += t.amount;
      if (t.kind === "expense") d.out += t.amount;
    }
    return [...map.values()];
  });

  const totals = $derived(
    filtered.reduce((s, t) => ((t.kind === "income" ? (s.in += t.amount) : t.kind === "expense" ? (s.out += t.amount) : 0), s), { in: 0, out: 0 })
  );
  const kinds = [["all", "All"], ["expense", "Expenses"], ["income", "Income"], ["transfer", "Transfers"]];
</script>

<div class="space-y-4 lg:space-y-5">
  <div class="panel space-y-3 p-4">
    <label class="relative block">
      <span class="sr-only">Search</span>
      <svg class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      <input class="field !pl-10" type="search" placeholder="Search notes, categories, accounts, amounts" bind:value={query} />
    </label>
    <!-- Type chips scroll sideways; the account picker gets its own full-width row on phones. -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div class="scroll-row -mx-1 flex min-w-0 flex-1 items-center gap-2 px-1">
        {#each kinds as [k, label]}
          <button class="chip shrink-0" aria-pressed={kind === k} onclick={() => (kind = k)}>{label}</button>
        {/each}
      </div>
      <select class="field select !min-h-10 !rounded-full !py-1.5 text-sm sm:!w-48" bind:value={account} aria-label="Account">
        <option value="">All accounts</option>
        {#each app.meta?.accounts ?? [] as a}<option value={a.id}>{a.name}</option>{/each}
      </select>
    </div>
    {#if app.categoryFilter}
      <div transition:slide={{ duration: 160 }}>
        <button class="chip" aria-pressed="true" onclick={() => (app.categoryFilter = null)}>
          {app.categoryFilter.name}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg><span class="sr-only">Clear category filter</span>
        </button>
      </div>
    {/if}
  </div>

  {#if error}
    <div class="panel p-5 text-danger" role="alert">{error}</div>
  {:else}
    <div class="flex flex-wrap gap-x-6 gap-y-1 px-1 text-ink-2">
      <span>{filtered.length} {filtered.length === 1 ? "transaction" : "transactions"}</span>
      <span class="num">In <strong class="text-ink">{peso(totals.in)}</strong></span>
      <span class="num">Out <strong class="text-ink">{peso(totals.out)}</strong></span>
    </div>

    {#if !loading && days.length === 0}
      <div class="panel p-8 text-center" in:fade>
        <p class="title text-xl">
          {list.length ? "Nothing matches those filters." : `No transactions in ${monthName(app.month)}.`}
        </p>
        <p class="mt-1 text-ink-2">{list.length ? "Clear the search or pick another type." : "Add one, or switch to another month."}</p>
        {#if !list.length}<button class="btn btn-primary mt-4" onclick={() => openAdd("expense")}>Add expense</button>{/if}
      </div>
    {/if}

    <div class="space-y-4 transition-opacity" class:opacity-50={loading}>
      {#each days as d, i (d.date)}
        <section class="panel p-2 sm:p-3" animate:flip={{ duration: 260 }} in:fly={{ y: 22, duration: reduced() ? 0 : 450, delay: reduced() ? 0 : Math.min(i, 8) * 55, easing: cubicOut }} out:fade={{ duration: 140 }}>
          <header class="flex items-baseline justify-between px-2 pb-1 pt-1">
            <h2 class="title">{dayLabel(d.date, today)}</h2>
            <span class="num text-sm text-ink-2">
              {#if d.in}+{peso(d.in)}{/if}{#if d.in && d.out}&ensp;{/if}{#if d.out}−{peso(d.out)}{/if}
            </span>
          </header>
          <ul>
            {#each d.items as tx (tx.id)}
              <li animate:flip={{ duration: 260 }} transition:slide={{ duration: 200 }}>
                <TxRow {tx} onclick={() => openEdit(tx)} />
              </li>
            {/each}
          </ul>
        </section>
      {/each}
    </div>
  {/if}
</div>
