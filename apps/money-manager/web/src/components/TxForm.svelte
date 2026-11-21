<script>
  import { slide } from "svelte/transition";
  import { untrack } from "svelte";
  import { app, changed, toast } from "../lib/store.svelte.js";
  import { api } from "../lib/api.js";
  import { iso, peso, splitEmoji } from "../lib/fmt.js";

  let { tx: txProp = null, kind: kindProp = "expense", onclose } = $props();
  // The form edits a copy: it takes its starting values once (App keys the sheet to its subject).
  const tx = untrack(() => txProp);
  const startKind = untrack(() => kindProp);

  const today = iso(new Date());
  const yesterday = iso(new Date(Date.now() - 864e5));
  const editing = !!tx;
  const isAdjust = tx?.kind === "adjust";
  const accounts = app.meta?.accounts ?? [];

  // Transfers are stored as two legs; editing from the "in" leg means the accounts are swapped.
  const fromLeg = tx?.kind === "transfer" && tx.direction === "in";
  let kind = $state(tx ? (tx.kind === "adjust" ? "expense" : tx.kind) : startKind);
  let amount = $state(tx ? String(tx.amount) : "");
  let date = $state(tx?.date ?? today);
  let accountId = $state(tx?.accountId ?? accounts[0]?.id ?? "");
  let fromId = $state(fromLeg ? tx.toAccountId : tx?.accountId ?? accounts[0]?.id ?? "");
  let toId = $state(fromLeg ? tx.accountId : tx?.toAccountId ?? accounts[1]?.id ?? "");
  let categoryId = $state(tx?.categoryId ?? "");
  let subcategoryId = $state(tx?.subcategoryId ?? "");
  let note = $state(tx?.note ?? "");
  let memo = $state(tx?.memo ?? "");
  let showMemo = $state(!!tx?.memo);
  let busy = $state(false);
  let error = $state("");
  let confirmDelete = $state(false);

  const cats = $derived(kind === "income" ? app.meta?.categories.income ?? [] : app.meta?.categories.expense ?? []);
  const subs = $derived(cats.find((c) => c.id === categoryId)?.subs ?? []);
  const verb = $derived({ expense: "expense", income: "income", transfer: "transfer" }[kind]);

  function setKind(k) {
    if (k === kind) return;
    kind = k;
    categoryId = subcategoryId = "";
    error = "";
  }

  async function save(e) {
    e?.preventDefault();
    error = "";
    const value = Number(String(amount).replace(/,/g, ""));
    if (!(value > 0)) return (error = "Enter an amount above zero.");
    if (kind !== "transfer" && !categoryId) return (error = "Pick a category.");
    if (kind === "transfer" && fromId === toId) return (error = "Pick two different accounts.");
    busy = true;
    try {
      const body =
        kind === "transfer"
          ? { kind, id: tx?.id, date, amount: value, fromId, toId, note, memo }
          : { kind, id: tx?.id, date, amount: value, accountId, categoryId, subcategoryId, note, memo };
      await api.saveTransaction(body);
      onclose();
      await changed(`${verb[0].toUpperCase() + verb.slice(1)} ${editing ? "updated" : "saved"}: ${peso(value)}`);
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }

  async function remove() {
    busy = true;
    try {
      await api.deleteTransaction(tx.id);
      onclose();
      await changed("Deleted");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      busy = false;
    }
  }
</script>

<form onsubmit={save} class="space-y-5">
  {#if isAdjust}
    <p class="rounded-xl bg-inset p-3 text-sm text-ink-2">
      This is a balance adjustment from {tx.account}. To change it, edit the account's balance in Accounts, or delete it here.
    </p>
  {:else}
    <div class="grid grid-cols-3 gap-1 rounded-full bg-inset p-1" role="radiogroup" aria-label="Type">
      {#each [["expense", "Expense", "var(--out)"], ["income", "Income", "var(--in)"], ["transfer", "Transfer", "var(--xfer)"]] as [k, label, color]}
        <button
          type="button"
          role="radio"
          aria-checked={kind === k}
          class="relative flex min-h-10 items-center justify-center gap-2 rounded-full text-sm font-semibold transition-colors
                 {kind === k ? 'bg-primary text-on-primary' : 'text-ink-2'}"
          onclick={() => setKind(k)}
        >
          <span class="size-2 rounded-full" style="background:{color}"></span>{label}
        </button>
      {/each}
    </div>

    <label class="block">
      <span class="label">Amount</span>
      <div class="flex items-baseline gap-2 border-b-2 border-line-strong pb-1 focus-within:border-[var(--focus)]">
        <span class="display text-4xl text-muted">{app.meta?.currency.symbol ?? "₱"}</span>
        <input
          class="display w-full bg-transparent text-5xl outline-none focus-visible:outline-none placeholder:text-line-strong"
          inputmode="decimal"
          autocomplete="off"
          placeholder="0.00"
          bind:value={amount}
          aria-label="Amount"
        />
      </div>
    </label>

    {#if kind === "transfer"}
      <div class="grid grid-cols-2 gap-3">
        <label class="block"><span class="label">From</span>
          <select class="field" bind:value={fromId}>{#each accounts as a}<option value={a.id}>{a.name}</option>{/each}</select>
        </label>
        <label class="block"><span class="label">To</span>
          <select class="field" bind:value={toId}>{#each accounts as a}<option value={a.id}>{a.name}</option>{/each}</select>
        </label>
      </div>
    {:else}
      <fieldset>
        <legend class="label mb-2 text-sm text-ink-2">Category</legend>
        <div class="flex flex-wrap gap-2">
          {#each cats as c (c.id)}
            {@const [emoji, name] = splitEmoji(c.name)}
            <button type="button" class="chip" aria-pressed={categoryId === c.id} onclick={() => ((categoryId = c.id), (subcategoryId = ""))}>
              {#if emoji}<span aria-hidden="true">{emoji}</span>{/if}{name}
            </button>
          {/each}
        </div>
        {#if subs.length}
          <div class="mt-2 flex flex-wrap gap-2 border-l-2 border-line pl-3" transition:slide={{ duration: 180 }}>
            {#each subs as s (s.id)}
              <button type="button" class="chip !min-h-8 !text-[0.85rem]" aria-pressed={subcategoryId === s.id} onclick={() => (subcategoryId = subcategoryId === s.id ? "" : s.id)}>{s.name}</button>
            {/each}
          </div>
        {/if}
      </fieldset>

      <fieldset>
        <legend class="label mb-2 text-sm text-ink-2">{kind === "income" ? "Into" : "Paid from"}</legend>
        <div class="flex flex-wrap gap-2">
          {#each accounts as a (a.id)}
            <button type="button" class="chip" aria-pressed={accountId === a.id} onclick={() => (accountId = a.id)}>{a.name}</button>
          {/each}
        </div>
      </fieldset>
    {/if}

    <fieldset>
      <legend class="label mb-2 text-sm text-ink-2">Date</legend>
      <div class="flex flex-wrap items-center gap-2">
        <button type="button" class="chip" aria-pressed={date === today} onclick={() => (date = today)}>Today</button>
        <button type="button" class="chip" aria-pressed={date === yesterday} onclick={() => (date = yesterday)}>Yesterday</button>
        <input type="date" class="field !w-auto !min-h-9 !py-1" bind:value={date} aria-label="Date" />
      </div>
    </fieldset>

    <label class="block">
      <span class="label">Note</span>
      <input class="field" bind:value={note} placeholder={kind === "expense" ? "What was it for?" : kind === "income" ? "From whom?" : "Optional"} />
    </label>
    {#if showMemo}
      <label class="block" transition:slide={{ duration: 160 }}>
        <span class="label">Details</span>
        <textarea class="field min-h-20" bind:value={memo}></textarea>
      </label>
    {:else}
      <button type="button" class="text-sm font-semibold text-ink-2 underline underline-offset-4" onclick={() => (showMemo = true)}>Add details</button>
    {/if}
  {/if}

  {#if error}<p class="text-sm font-semibold text-danger" role="alert">{error}</p>{/if}

  <div class="flex items-center gap-3 pt-1">
    {#if editing}
      {#if confirmDelete}
        <button type="button" class="btn btn-danger" disabled={busy} onclick={remove}>Delete for good</button>
        <button type="button" class="btn btn-quiet" onclick={() => (confirmDelete = false)}>Keep</button>
      {:else}
        <button type="button" class="btn btn-danger" onclick={() => (confirmDelete = true)}>Delete</button>
      {/if}
    {/if}
    {#if !isAdjust}
      <button type="submit" class="btn btn-primary ml-auto min-w-40" disabled={busy}>
        {busy ? "Saving…" : `${editing ? "Update" : "Save"} ${verb}`}
      </button>
    {/if}
  </div>
</form>
