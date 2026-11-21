<script>
  import { slide } from "svelte/transition";
  import { app, changed, toast, signOut, setSkin } from "../lib/store.svelte.js";
  import Mascot from "../components/Mascot.svelte";
  import { session } from "../lib/api.js";
  import Avatar from "../components/Avatar.svelte";
  import { monthName, monthRange } from "../lib/fmt.js";

  let theme = $state(document.documentElement.dataset.theme || "auto");
  let file = $state(null);
  let busy = $state(false);
  let confirmRestore = $state(false);

  function setTheme(t) {
    theme = t;
    if (t === "auto") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = t;
    try {
      t === "auto" ? localStorage.removeItem("pitaka-theme") : localStorage.setItem("pitaka-theme", t);
    } catch {
      /* private mode: theme just won't be remembered */
    }
  }

  async function restore() {
    busy = true;
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/moneyBook/uploadSqlFile", { method: "POST", body: fd });
      const out = await res.json().catch(() => ({}));
      if (!res.ok || !out.success) throw new Error(out.msg || "That file couldn't be restored.");
      file = null;
      confirmRestore = false;
      await changed("Backup restored");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      busy = false;
    }
  }

  const range = $derived(monthRange(app.month));

  // Profile photo: center-crop to a square and shrink to 320px on the device, then upload.
  let photoInput = $state();
  let photoBusy = $state(false);
  async function pickPhoto(e) {
    const f = e.currentTarget.files?.[0];
    e.currentTarget.value = "";
    if (!f) return;
    photoBusy = true;
    try {
      const bmp = await createImageBitmap(f, { imageOrientation: "from-image" }).catch(() => null);
      if (!bmp) throw new Error("That file isn't a photo this browser can read.");
      const side = Math.min(bmp.width, bmp.height);
      const out = Math.min(320, side);
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = out;
      canvas.getContext("2d").drawImage(bmp, (bmp.width - side) / 2, (bmp.height - side) / 2, side, side, 0, 0, out, out);
      const { avatar } = await session.setAvatar(canvas.toDataURL("image/jpeg", 0.86));
      app.user = { ...app.user, avatar };
      toast("Profile photo updated");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      photoBusy = false;
    }
  }
  async function removePhoto() {
    try {
      await session.setAvatar(null);
      app.user = { ...app.user, avatar: 0 };
      toast("Profile photo removed");
    } catch (err) {
      toast(err.message, "error");
    }
  }

  let pwOpen = $state(false);
  let current = $state("");
  let next = $state("");
  let pwBusy = $state(false);
  async function changePassword(e) {
    e.preventDefault();
    pwBusy = true;
    try {
      await session.changePassword(current, next);
      current = next = "";
      pwOpen = false;
      toast("Password changed. Other devices were signed out.");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      pwBusy = false;
    }
  }
</script>

<div class="max-w-2xl space-y-4 lg:space-y-5">
  <section class="panel p-5">
    <h2 class="title text-lg">Account</h2>
    <!-- Photo and name on one row; actions below (a 2-up grid on phones, inline on wider screens). -->
    <div class="mt-4 flex items-center gap-4">
      <button class="group relative shrink-0 rounded-full" onclick={() => photoInput.click()} aria-label="Change profile photo" disabled={photoBusy}>
        <Avatar size={68} />
        <span class="absolute inset-0 grid place-items-center rounded-full bg-black/45 text-white opacity-0 transition-opacity group-hover:opacity-100 {photoBusy ? '!opacity-100' : ''}" aria-hidden="true">
          {#if photoBusy}
            <svg class="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6"><path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" /></svg>
          {:else}
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></svg>
          {/if}
        </span>
        <span class="absolute -bottom-0.5 -right-0.5 grid size-6 place-items-center rounded-full bg-card text-ink shadow ring-1 ring-line" aria-hidden="true">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
        </span>
      </button>
      <input bind:this={photoInput} type="file" accept="image/*" class="hidden" onchange={pickPhoto} />
      <div class="min-w-0 flex-1">
        <p class="truncate text-lg font-semibold">{app.user?.username}</p>
        <p class="text-sm text-muted">Your book is private to this account.</p>
        <div class="mt-1 flex gap-3 text-sm font-semibold">
          <button class="text-ink underline-offset-2 hover:underline" onclick={() => photoInput.click()}>{app.user?.avatar ? "Change photo" : "Add photo"}</button>
          {#if app.user?.avatar}<button class="text-muted underline-offset-2 hover:underline" onclick={removePhoto}>Remove</button>{/if}
        </div>
      </div>
    </div>
    <div class="mt-4 grid grid-cols-2 gap-2 sm:flex sm:justify-end">
      <button class="btn btn-quiet" aria-expanded={pwOpen} onclick={() => (pwOpen = !pwOpen)}>Change password</button>
      <button class="btn btn-danger" onclick={signOut}>Sign out</button>
    </div>
    {#if pwOpen}
      <form class="mt-4 grid gap-3 sm:grid-cols-2" onsubmit={changePassword} transition:slide={{ duration: 240 }}>
        <label class="block"><span class="label">Current password</span><input class="field" type="password" bind:value={current} autocomplete="current-password" required /></label>
        <label class="block"><span class="label">New password</span><input class="field" type="password" bind:value={next} autocomplete="new-password" minlength="8" required /></label>
        <div class="sm:col-span-2"><button class="btn btn-primary" disabled={pwBusy}>{pwBusy ? "Saving…" : "Save new password"}</button></div>
      </form>
    {/if}
  </section>


  <section class="panel p-5">
    <h2 class="title text-lg">Appearance</h2>
    {#if app.animeUnlocked}
      <!-- Only shown once the secret has been found (7 taps on the logo). -->
      <p class="mt-3 text-sm font-semibold text-ink-2">Style</p>
      <div class="mt-2 grid grid-cols-2 gap-3 sm:max-w-md" role="radiogroup" aria-label="Style">
        {#each [["glass", "Glass", "Frosted panels over soft color"], ["anime", "Anime", "Light: black-and-white manga. Dark: chuunibyou."]] as [k, label, note]}
          <button
            role="radio"
            aria-checked={app.skin === k}
            onclick={() => setSkin(k)}
            class="relative overflow-hidden rounded-2xl p-3 text-left ring-2 transition-[box-shadow,transform] duration-300 active:scale-[.97] {app.skin === k ? 'ring-[var(--primary)]' : 'ring-[var(--line)] hover:ring-[var(--line-strong)]'}"
          >
            <span class="mb-2 flex h-16 overflow-hidden rounded-xl" style="background: radial-gradient(circle at 20% 30%,#9cc8ff,transparent 60%),radial-gradient(circle at 80% 70%,#d4c6ff,transparent 60%),#e9edf5">
              {#if k === "anime"}
                <span class="flex-1 border-r-2 border-black bg-white" style="background: repeating-conic-gradient(from 0deg at 50% 50%, #0a0a0a 0 1deg, transparent 1deg 7deg), #fff"></span>
                <span class="grid flex-1 place-items-center" style="background:#07040c"><Mascot size={36} face /></span>
              {/if}
            </span>
            <span class="block font-semibold">{label}</span>
            <span class="block text-[13px] text-muted">{note}</span>
          </button>
        {/each}
      </div>
      <p class="mt-1.5 text-[13px] text-muted">Or tap the Pitaka logo 7 times.</p>
    {/if}
    <p class="mt-4 text-sm font-semibold text-ink-2">Theme</p>
    <div class="mt-2 flex gap-2" role="radiogroup" aria-label="Theme">
      {#each [["auto", "Match device"], ["light", "Light"], ["dark", "Dark"]] as [t, label]}
        <button class="chip" role="radio" aria-checked={theme === t} onclick={() => setTheme(t)}>{label}</button>
      {/each}
    </div>
  </section>

  <section class="panel p-5">
    <h2 class="title text-lg">Backup</h2>
    <p class="mt-1 text-ink-2">Downloads the whole database as <code>money.sqlite</code>. You can restore it here, or upload it on the phone's PC Manager page.</p>
    <a class="btn btn-quiet mt-3" href="/moneyBook/money.sqlite" download>Download backup</a>
  </section>

  <section class="panel p-5">
    <h2 class="title text-lg">Restore from a backup</h2>
    <p class="mt-1 text-ink-2">Replaces everything here with the file you pick. The current data is kept on the server as a dated copy first.</p>
    <input class="mt-3 block w-full text-sm file:mr-3 file:rounded-full file:border-0 file:bg-inset file:px-4 file:py-2 file:font-semibold" type="file" accept=".sqlite,.db,application/x-sqlite3" onchange={(e) => ((file = e.currentTarget.files[0]), (confirmRestore = false))} />
    {#if file}
      <div class="mt-3 flex flex-wrap items-center gap-3">
        {#if confirmRestore}
          <button class="btn btn-danger" disabled={busy} onclick={restore}>{busy ? "Restoring…" : "Replace my data"}</button>
          <button class="btn btn-quiet" onclick={() => (confirmRestore = false)}>Cancel</button>
        {:else}
          <button class="btn btn-quiet" onclick={() => (confirmRestore = true)}>Restore {file.name}</button>
        {/if}
      </div>
    {/if}
  </section>

  <section class="panel p-5">
    <h2 class="title text-lg">Export</h2>
    <p class="mt-1 text-ink-2">A spreadsheet (CSV) of every transaction in {monthName(app.month)}.</p>
    <form method="POST" action="/moneyBook/getExcelFile" class="mt-3">
      <input type="hidden" name="startDate" value={range.from} />
      <input type="hidden" name="endDate" value={range.to} />
      <input type="hidden" name="mbid" value="1" />
      <input type="hidden" name="assetId" value="" />
      <button class="btn btn-quiet">Export {monthName(app.month)}</button>
    </form>
  </section>

  <section class="panel p-5">
    <h2 class="title text-lg">Classic view</h2>
    <p class="mt-1 text-ink-2">The original Money Manager desktop page still works, on the same data.</p>
    <a class="btn btn-quiet mt-3" href="/classic/">Open classic view</a>
  </section>
</div>
