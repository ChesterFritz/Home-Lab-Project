<script>
  import { untrack } from "svelte";
  import { app, changed, toast } from "../lib/store.svelte.js";
  import { api } from "../lib/api.js";
  import { peso } from "../lib/fmt.js";

  let { account: accountProp = null, onclose } = $props();
  const account = untrack(() => accountProp);
  const groups = (app.meta?.groups ?? []).filter((g) => !g.isCard || account?.isCard);
  let name = $state(account?.name ?? "");
  let groupId = $state(account?.groupId ?? groups[0]?.id ?? "");
  let balance = $state(account ? String(account.balance) : "0");
  let busy = $state(false);
  let error = $state("");
  let confirmDelete = $state(false);

  const diff = $derived(account ? Number(balance || 0) - account.balance : 0);

  async function save(e) {
    e.preventDefault();
    if (!name.trim()) return (error = "Give the account a name.");
    if (balance !== "" && isNaN(Number(balance))) return (error = "Balance must be a number, e.g. -3955 for money you owe.");
    busy = true;
    try {
      await api.saveAccount({ id: account?.id, name: name.trim(), groupId, balance: balance === "" ? undefined : Number(balance) });
      onclose();
      await changed(account ? "Account updated" : "Account added");
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }

  async function remove() {
    busy = true;
    try {
      await api.deleteAccount(account.id);
      onclose();
      await changed("Account removed");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      busy = false;
    }
  }
</script>

<form onsubmit={save} class="space-y-5">
  <label class="block"><span class="label">Name</span>
    <input class="field" bind:value={name} placeholder="e.g. GCash, BPI Savings" />
  </label>
  <label class="block"><span class="label">Group</span>
    <select class="field" bind:value={groupId}>{#each groups as g}<option value={g.id}>{g.name}</option>{/each}</select>
  </label>
  <label class="block">
    <span class="label">{account ? "Current balance" : "Starting balance"}</span>
    <input class="field num" inputmode="decimal" bind:value={balance} />
    <span class="mt-1 block text-sm text-muted">
      Use a negative number for money you owe.
      {#if account && Math.abs(diff) >= 0.005}
        Saving records a {peso(diff, { sign: true })} balance adjustment today.
      {/if}
    </span>
  </label>

  {#if error}<p class="text-sm font-semibold text-danger" role="alert">{error}</p>{/if}

  <div class="flex items-center gap-3">
    {#if account}
      {#if confirmDelete}
        <button type="button" class="btn btn-danger" disabled={busy} onclick={remove}>Remove account</button>
        <button type="button" class="btn btn-quiet" onclick={() => (confirmDelete = false)}>Keep</button>
      {:else}
        <button type="button" class="btn btn-danger" onclick={() => (confirmDelete = true)}>Remove</button>
      {/if}
    {/if}
    <button class="btn btn-primary ml-auto min-w-36" disabled={busy}>{busy ? "Saving…" : account ? "Save changes" : "Add account"}</button>
  </div>
  {#if confirmDelete}
    <p class="text-sm text-ink-2">Its past transactions stay in your history, but it disappears from lists and balances.</p>
  {/if}
</form>
