<script module>
  let introPlayed = false; // the page-load sequence runs once per visit, not on every tab switch
</script>

<script>
  import { animate, stagger } from "motion";
  import { app, go, openAdd, openEdit, openAccount } from "../lib/store.svelte.js";
  import { api } from "../lib/api.js";
  import { monthName, monthRange, peso, shiftMonth, monthShort } from "../lib/fmt.js";
  import { reduced, reveal } from "../lib/motion.js";
  import Money from "../components/Money.svelte";
  import ChartCard from "../components/ChartCard.svelte";
  import FlowChart from "../charts/FlowChart.svelte";
  import TrendChart from "../charts/TrendChart.svelte";
  import CategoryBars from "../charts/CategoryBars.svelte";
  import BalanceLine from "../charts/BalanceLine.svelte";
  import FlowList from "../charts/FlowList.svelte";
  import Spark from "../charts/Spark.svelte";
  import { word } from "../lib/words.js";
  import TxRow from "../components/TxRow.svelte";

  let summary = $state(null);
  let trend = $state([]);
  let worth = $state([]);
  let recent = $state([]);
  let loading = $state(true);
  let error = $state("");
  let hero = $state();

  $effect(() => {
    const month = app.month;
    app.version; // refetch after edits
    const { from, to } = monthRange(month);
    let stale = false;
    Promise.all([api.summary(from, to), api.trend(month, 12), api.networth(12), api.transactions(from, to)])
      .then(([s, t, w, tx]) => {
        if (stale) return;
        summary = s;
        trend = t;
        worth = w;
        recent = tx.slice(0, 6);
        error = "";
      })
      .catch((e) => !stale && (error = e.message))
      .finally(() => !stale && (loading = false));
    return () => (stale = true);
  });

  $effect(() => {
    if (!hero || !summary || introPlayed || reduced()) return;
    introPlayed = true;
    // One moment per visit: the glass cards float up into place, one after another.
    animate(hero.querySelectorAll("[data-rise]"), { opacity: [0, 1], y: [24, 0], scale: [0.97, 1] }, { duration: 0.7, delay: stagger(0.09), ease: [0.22, 1, 0.36, 1] });
  });

  const empty = $derived(summary && summary.income === 0 && summary.expense === 0);
  // When the chosen month is empty, offer the most recent month that has activity.
  const lastActive = $derived(
    [...trend].reverse().find((m) => m.month < app.month && (m.income > 0 || m.expense > 0))?.month
  );
  const spentShare = $derived(summary && summary.income > 0 ? Math.round((summary.expense / summary.income) * 100) : null);
  const noAccounts = $derived(!app.meta?.accounts.length);
  // A brand-new book has nothing to chart yet; the history cards appear once there's a year to show.
  const hasHistory = $derived(trend.some((m) => m.income > 0 || m.expense > 0));

  const month = $derived(monthName(app.month, { month: "long" }));
  const prev = $derived(trend.find((m) => m.month === shiftMonth(app.month, -1)));
  const hadPrev = $derived(prev && (prev.income > 0 || prev.expense > 0));
  const stats = $derived(
    summary
      ? [
          { label: word("cameIn", "Came in"), value: summary.income, color: "var(--in)", series: trend.map((m) => m.income), delta: hadPrev ? summary.income - prev.income : null },
          { label: word("wentOut", "Went out"), value: summary.expense, color: "var(--out)", series: trend.map((m) => m.expense), delta: hadPrev ? summary.expense - prev.expense : null },
          { label: summary.net >= 0 ? word("leftOver", "Left over") : word("overspent", "Overspent"), value: summary.net, sign: true, color: "var(--ink)", series: trend.map((m) => m.income - m.expense), delta: hadPrev ? summary.net - (prev.income - prev.expense) : null },
        ]
      : []
  );

  function pickCategory(node) {
    go("transactions", { categoryFilter: { id: node.id, name: node.name } });
  }
</script>

<div class="space-y-4 lg:space-y-5">

  {#if error}
    <div class="panel p-5 text-danger" role="alert">{error}</div>
  {:else if loading && !summary}
    <div class="panel h-[260px] animate-pulse" aria-busy="true"></div>
  {:else if summary}
    {#if noAccounts || empty}
      <section bind:this={hero} class="panel px-6 py-8 sm:px-9 sm:py-10">
        {#if noAccounts}
          <h2 data-rise class="display text-[clamp(1.8rem,4vw,2.6rem)]">Start with where your money lives.</h2>
          <p data-rise class="mt-3 max-w-lg text-ink-2">Add an account for each place you keep money: cash, GCash, a savings account, a loan. Every expense and income is logged against one of them.</p>
          <button data-rise class="btn btn-primary mt-6" onclick={() => { go("accounts"); openAccount(); }}>Add your first account</button>
        {:else}
          <h2 data-rise class="display text-[clamp(1.8rem,4vw,2.6rem)]">Nothing logged in {month} yet.</h2>
          <p data-rise class="mt-3 max-w-lg text-ink-2">Add what you spend and earn, and this page fills in with where the money went.</p>
          <div data-rise class="mt-6 flex flex-wrap gap-2">
            <button class="btn btn-primary" onclick={() => openAdd("expense")}>Add expense</button>
            {#if lastActive}<button class="btn btn-quiet" onclick={() => (app.month = lastActive)}>View {monthName(lastActive, { month: "long" })}</button>{/if}
          </div>
        {/if}
      </section>
    {:else}
      <!-- Three glass stat cards: the figure, how it compares with last month, and its year. -->
      <div bind:this={hero} class="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4">
        {#each stats as st (st.label)}
          <section data-rise class="panel lift flex flex-col p-4 sm:p-5 {st.sign ? 'max-sm:col-span-2' : ''}" aria-label={st.label}>
            <p class="flex items-center gap-2 text-sm font-medium text-ink-2">
              <span class="size-2.5 rounded-full" style="background:{st.color}"></span>{st.label}
            </p>
            <p class="display mt-1.5 text-[1.3rem] sm:mt-2 sm:text-[clamp(1.6rem,2.6vw,2.3rem)]"><Money value={st.value} sign={st.sign} /></p>
            <p class="mt-1 text-[13px] text-muted">
              {#if st.delta === null}No {monthName(shiftMonth(app.month, -1), { month: "long" })} figure to compare{:else}{st.delta === 0 ? "Same as" : `${st.delta > 0 ? "Up" : "Down"} ${peso(Math.abs(st.delta))} on`} {monthName(shiftMonth(app.month, -1), { month: "long" })}{/if}
            </p>
            <div class="mt-4 max-sm:hidden"><Spark values={st.series} keys={trend.map((m) => m.month)} selected={app.month} color={st.color} label="{st.label}, last 12 months" /></div>
          </section>
        {/each}
      </div>
    {/if}

    {#if !empty && !noAccounts}
      <section use:reveal class="panel p-5 sm:p-6">
        <h2 class="title text-lg">{word("flow", "Where the money went")}</h2>
        <p class="mb-3 text-sm text-muted">Tap a category to see its transactions.</p>
        <!-- Phones and tablets get the unrolled list; the flow diagram needs a wide screen. -->
        <div class="lg:hidden"><FlowList {summary} onpick={pickCategory} /></div>
        <div class="hidden h-full lg:block"><FlowChart {summary} monthLabel={month} onpick={pickCategory} /></div>
      </section>
    {/if}

    {#if hasHistory}
      <div class="grid gap-4 lg:gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div use:reveal class="h-full">
        <ChartCard
          title={word("trend", "Money in and out")}
          note="12 months up to {monthName(app.month)}. Tap a month to open it."
          legend={[{ label: "Money in", color: "var(--in)" }, { label: "Money out", color: "var(--out)" }]}
          table={{ columns: ["Month", "In", "Out", "Net"], rows: trend.map((m) => [monthName(m.month), peso(m.income), peso(m.expense), peso(m.income - m.expense, { sign: true })]) }}
        >
          <TrendChart data={trend} selected={app.month} onselect={(m) => (app.month = m)} />
        </ChartCard>
        </div>

        <!-- On phones the list above already ranks the categories. -->
        <div class="hidden h-full lg:block">
          <div use:reveal class="h-full">
          <ChartCard
            title={word("categories", "Spending by category")}
            note={summary.expense > 0 ? "Tap a category to see its transactions." : ""}
            table={summary.expense_by_category.length ? { columns: ["Category", "Spent", "Share"], rows: summary.expense_by_category.map((c) => [c.name, peso(c.amount), Math.round((c.amount / summary.expense) * 100) + "%"]) } : null}
          >
            {#if summary.expense_by_category.length}
              <CategoryBars items={summary.expense_by_category.slice(0, 6)} total={summary.expense} onpick={pickCategory} />
              {#if summary.expense_by_category.length > 6}
                <p class="mt-3 text-sm text-muted">Plus {summary.expense_by_category.length - 6} smaller categories. Open Table to see them all.</p>
              {/if}
            {:else}
              <p class="py-6 text-ink-2">No spending in {month}.</p>
            {/if}
          </ChartCard>
          </div>
        </div>
      </div>

      <div class="grid gap-4 lg:gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div use:reveal class="h-full">
        <ChartCard
          title={word("networth", "Net worth")}
          note="Everything you have minus everything you owe"
          table={{ columns: ["Month", "Have", "Owe", "Net worth"], rows: worth.map((w) => [monthName(w.month), peso(w.assets), peso(w.debts), peso(w.total)]) }}
        >
          <p class="display text-3xl"><Money value={app.meta?.netWorth ?? 0} /></p>
          <div class="mt-3">
            <BalanceLine
              name="Net worth"
              points={worth.map((w) => ({ key: w.month, value: w.total }))}
              label={(p) => monthName(p.key)}
              tick={(p) => monthShort(p.key)}
              height={250}
            />
          </div>
        </ChartCard>
        </div>

        <section use:reveal class="panel p-5">
          <div class="flex items-center justify-between">
            <h2 class="title text-lg">{app.anime === "chuuni" ? word("latest", "") : `Latest in ${month}`}</h2>
            <button class="chip !min-h-9" onclick={() => go("transactions")}>See all</button>
          </div>
          {#if recent.length}
            <ul class="mt-2 divide-y divide-line">
              {#each recent as tx (tx.id)}<li><TxRow {tx} onclick={() => openEdit(tx)} /></li>{/each}
            </ul>
          {:else}
            <p class="py-6 text-ink-2">No transactions this month.</p>
          {/if}
        </section>
      </div>
    {/if}
  {/if}
</div>
