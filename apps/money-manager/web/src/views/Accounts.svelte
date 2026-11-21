<script>
  import { fade, fly } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { reduced, reveal } from "../lib/motion.js";
  import { app, openAccount, openEdit } from "../lib/store.svelte.js";
  import { api } from "../lib/api.js";
  import { iso, monthRange, peso, ym } from "../lib/fmt.js";
  import Money from "../components/Money.svelte";
  import ChartCard from "../components/ChartCard.svelte";
  import BalanceLine from "../charts/BalanceLine.svelte";
  import TxRow from "../components/TxRow.svelte";

  let selectedId = $state("");
  let history = $state([]);
  let recent = $state([]);

  const accounts = $derived(app.meta?.accounts ?? []);
  const groups = $derived(
    (app.meta?.groups ?? [])
      .map((g) => ({ ...g, accounts: accounts.filter((a) => a.groupId === g.id) }))
      .filter((g) => g.accounts.length)
  );
  const have = $derived(accounts.filter((a) => a.balance > 0).reduce((s, a) => s + a.balance, 0));
  const owe = $derived(accounts.filter((a) => a.balance < 0).reduce((s, a) => s + a.balance, 0));
  const selected = $derived(accounts.find((a) => a.id === selectedId) ?? accounts[0]);

  $effect(() => {
    const id = selected?.id;
    app.version;
    if (!id) return;
    let stale = false;
    const from = iso(new Date(Date.now() - 90 * 864e5));
    Promise.all([api.accountHistory(id, 26), api.transactions(from, monthRange(ym(new Date())).to, id)]).then(([h, t]) => {
      if (stale) return;
      history = h;
      recent = t.slice(0, 8);
    });
    return () => (stale = true);
  });

  const shortDate = (p) => new Date(p.key + "T00:00:00").toLocaleDateString("en-PH", { month: "short", day: "numeric" });
</script>

<div class="space-y-4 lg:space-y-5">
  <section class="panel lift grid grid-cols-2 gap-x-4 gap-y-5 p-5 sm:grid-cols-3 sm:p-7">
    <div class="col-span-2 sm:col-span-1">
      <h2 class="text-sm font-medium text-muted">Net worth</h2>
      <p class="display mt-1 text-[clamp(2.3rem,8vw,3.2rem)]"><Money value={app.meta?.netWorth ?? 0} /></p>
    </div>
    <div>
      <h2 class="flex items-center gap-2 text-sm font-bold text-muted"><span class="h-3 w-1.5 rounded-full bg-in"></span>You have</h2>
      <p class="num mt-1 text-xl font-extrabold sm:text-3xl"><Money value={have} /></p>
    </div>
    <div>
      <h2 class="flex items-center gap-2 text-sm font-bold text-muted"><span class="h-3 w-1.5 rounded-full bg-out"></span>You owe</h2>
      <p class="num mt-1 text-xl font-extrabold sm:text-3xl"><Money value={Math.abs(owe)} /></p>
    </div>
  </section>

  <div class="grid gap-4 lg:gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
    <section class="panel p-3 sm:p-4">
      <div class="flex items-center justify-between px-2 pb-2">
        <h2 class="title text-lg">Accounts</h2>
        <button class="btn btn-quiet !min-h-9 text-sm" onclick={() => openAccount()}>Add account</button>
      </div>
      {#each groups as g (g.id)}
        <h3 class="px-2 pb-1 pt-3 text-sm font-semibold text-muted">{g.name}</h3>
        <ul>
          {#each g.accounts as a, i (a.id)}
            <li in:fly={{ x: -14, duration: reduced() ? 0 : 420, delay: reduced() ? 0 : i * 60 + 80, easing: cubicOut }}>
              <button
                class="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-3 text-left transition-colors duration-200 hover:bg-inset {selected?.id === a.id ? 'bg-inset' : ''}"
                aria-current={selected?.id === a.id}
                onclick={() => (selectedId = a.id)}
              >
                <span class="flex items-center gap-3">
                  <span class="h-7 w-1 rounded-full" style="background:{a.balance < 0 ? 'var(--out)' : a.balance > 0 ? 'var(--in)' : 'var(--line-strong)'}"></span>
                  <span class="font-semibold">{a.name}</span>
                </span>
                <span class="num font-semibold">{peso(a.balance)}</span>
              </button>
            </li>
          {/each}
        </ul>
      {/each}
    </section>

    {#if selected}
      {#key selected.id}
        <div class="space-y-4 lg:space-y-5" in:fade={{ duration: 180 }}>
          <ChartCard
            title={selected.name}
            note={selected.balance < 0 ? `You owe ${peso(-selected.balance)}` : "Balance over the last 26 weeks"}
            table={{ columns: ["Week of", "Balance"], rows: history.map((h) => [h.date, peso(h.balance)]) }}
          >
            {#snippet actions()}
              <button class="chip !min-h-8 !text-[0.82rem]" onclick={() => openAccount(selected)}>Edit</button>
            {/snippet}
            <p class="display text-4xl"><Money value={selected.balance} /></p>
            <div class="mt-3">
              <BalanceLine name={selected.name} points={history.map((h) => ({ key: h.date, value: h.balance }))} label={shortDate} tick={shortDate} height={190} />
            </div>
          </ChartCard>
          <section use:reveal class="panel p-4 sm:p-5">
            <h2 class="title text-lg">Last 90 days</h2>
            {#if recent.length}
              <ul class="mt-2 divide-y divide-line">
                {#each recent as tx (tx.id)}<li><TxRow {tx} onclick={() => openEdit(tx)} /></li>{/each}
              </ul>
            {:else}
              <p class="py-4 text-ink-2">No activity in the last 90 days.</p>
            {/if}
          </section>
        </div>
      {/key}
    {/if}
  </div>
</div>
