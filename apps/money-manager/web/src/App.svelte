<script>
  import { cubicOut } from "svelte/easing";
  import { reduced } from "./lib/motion.js";
  import { animate } from "motion";
  import { app, boot, loadMeta, openAdd, signOut, setSkin, toast } from "./lib/store.svelte.js";
  import { word } from "./lib/words.js";
  import { stamp, circleBurst, awaken } from "./lib/fx.js";
  import Auth from "./views/Auth.svelte";
  import Avatar from "./components/Avatar.svelte";
  import Mascot from "./components/Mascot.svelte";
  import Money from "./components/Money.svelte";
  import Sheet from "./components/Sheet.svelte";
  import TxForm from "./components/TxForm.svelte";
  import AccountForm from "./components/AccountForm.svelte";
  import Toast from "./components/Toast.svelte";
  import Ambient from "./components/Ambient.svelte";
  import MonthSwitch from "./components/MonthSwitch.svelte";
  import Overview from "./views/Overview.svelte";
  import Transactions from "./views/Transactions.svelte";
  import Accounts from "./views/Accounts.svelte";
  import Settings from "./views/Settings.svelte";

  boot();

  const nav = [
    ["overview", "Overview", "M4 13h4v7H4zM10 4h4v16h-4zM16 9h4v11h-4z"],
    ["transactions", "Transactions", "M4 6h16M4 12h16M4 18h10"],
    ["accounts", "Accounts", "M3 7h18v12H3zM3 11h18M7 15h3"],
    ["settings", "Settings", "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19 12l2-1-2-4-2 .5-1.5-1L15 4h-6l-.5 2.5-1.5 1L5 7l-2 4 2 1v0l-2 1 2 4 2-.5 1.5 1L9 20h6l.5-2.5 1.5-1 2 .5 2-4z"],
  ];
  const short = { overview: "Home", transactions: "Activity", accounts: "Accounts", settings: "Settings" };
  const label = (id, plain) => word(id, plain);
  const views = { overview: Overview, transactions: Transactions, accounts: Accounts, settings: Settings };
  const View = $derived(views[app.view]);
  const monthly = $derived(app.view === "overview" || app.view === "transactions");
  const close = () => (app.sheet = null);

  // Page change: the new view rises out of a soft blur, like a glass pane coming into focus.
  function enter(node) {
    if (reduced()) return { duration: 0 };
    return { duration: 420, easing: cubicOut, css: (t, u) => `opacity:${t}; transform:translateY(${u * 14}px); filter:blur(${u * 8}px)` };
  }

  // One pill per nav slides to the active item instead of each item lighting up on its own.
  let rail = $state(), bar = $state();
  let railPill = $state(null), barPill = $state(null);
  $effect(() => {
    app.view;
    const measure = () => {
      const r = rail?.querySelector('[aria-current="page"]');
      railPill = r ? { top: r.offsetTop, h: r.offsetHeight } : null;
      const b = bar?.querySelector('[aria-current="page"]');
      barPill = b ? { left: b.offsetLeft, w: b.offsetWidth } : null;
    };
    measure();
    addEventListener("resize", measure);
    return () => removeEventListener("resize", measure);
  });

  // Mac: a soft highlight on the glass follows the pointer.
  function sheen(e) {
    if (e.pointerType !== "mouse") return;
    const p = e.target.closest?.(".panel, .glass");
    if (!p) return;
    const r = p.getBoundingClientRect();
    p.style.setProperty("--mx", `${e.clientX - r.left}px`);
    p.style.setProperty("--my", `${e.clientY - r.top}px`);
  }

  // The Add button answers a tap: it squashes, a ring bursts out, then the form opens.
  let burst = $state(0);
  // Anime style: the + answers with a manga sound effect, or a crimson summoning circle.
  function animeTap(btn) {
    const r = btn.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    if (app.anime === "manga") stamp("ドン!", Math.min(cx + 40, innerWidth - 70), cy - 50, 54);
    else circleBurst(cx, cy, 200);
  }

  // A save gets its own moment: カチャ! (ka-cha, the till) or a sealing circle.
  let lastVersion = app.version;
  $effect(() => {
    if (app.version === lastVersion) return;
    lastVersion = app.version;
    if (app.anime === "manga") stamp("カチャ!", innerWidth / 2, innerHeight * 0.42, 84);
    else if (app.anime === "chuuni") circleBurst(innerWidth / 2, innerHeight * 0.45, Math.min(innerWidth, innerHeight) * 0.7);
  });
  // Chuunibyou page change: a summoning circle flares behind the new page.
  let lastView = app.view;
  $effect(() => {
    if (app.view === lastView) return;
    lastView = app.view;
    if (app.anime === "chuuni") circleBurst(innerWidth / 2, innerHeight / 2, Math.max(innerWidth, innerHeight) * 0.9);
  });

  // The secret: tap the logo 7 times in a row (each within a second of the last).
  let taps = 0, lastTap = 0;
  function tapLogo(e) {
    const now = performance.now();
    taps = now - lastTap < 1000 ? taps + 1 : 1;
    lastTap = now;
    const img = e.currentTarget.querySelector("img");
    if (img && !reduced()) animate(img, { rotate: [0, (taps % 2 ? 1 : -1) * (4 + taps * 3), 0], scale: [1, 1 + taps * 0.05, 1] }, { duration: 0.35 });
    const on = app.skin === "anime";
    if (taps >= 4 && taps < 7) toast(on ? `${7 - taps}… the seal is weakening` : `${7 - taps}…`);
    if (taps === 7) {
      taps = 0;
      e.preventDefault();
      app.toast = null;
      const mode = on ? app.anime : app.dark ? "chuuni" : "manga";
      awaken(mode, !on, () => setSkin(on ? "glass" : "anime"));
    }
  }

  function add(e) {
    burst++;
    if (app.anime && !reduced()) animeTap(e.currentTarget);
    if (!reduced()) animate(e.currentTarget, { scale: [1, 0.84, 1.06, 1] }, { duration: 0.45, ease: "easeOut" });
    // A beat so the tap reads before the sheet slides over the button.
    setTimeout(() => openAdd("expense"), reduced() ? 0 : 140);
  }

  // Every button answers a press: a ripple spreads from where you touched it.
  function press(e) {
    const b = e.target.closest?.(".btn, .chip");
    if (!b || b.disabled || b.classList.contains("add-btn") || reduced()) return;
    const r = b.getBoundingClientRect();
    const d = Math.max(r.width, r.height) * 2.2;
    const ink = document.createElement("span");
    ink.className = "ink";
    ink.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`;
    b.appendChild(ink);
    ink.addEventListener("animationend", () => ink.remove());
  }

  function key(e) {
    if (e.key === "n" && !app.sheet && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName) && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      openAdd("expense");
    }
  }
</script>

<svelte:window onkeydown={key} onpointermove={sheen} onpointerdown={press} />

{#snippet icon(path, size = 20)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d={path} /></svg>
{/snippet}
{#snippet plus(size = 18)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
{/snippet}

<Ambient />

{#if app.user === null}
  <Auth />
{:else if app.user}

<!-- Mac and iPad landscape: a floating glass sidebar. iPad portrait: the same, as an icon rail. -->
<aside
  class="glass fixed bottom-4 left-4 top-4 z-30 hidden flex-col rounded-[28px] p-3 md:flex md:w-[76px] lg:w-[236px] lg:p-4"
  style="top: max(1rem, env(safe-area-inset-top)); bottom: max(1rem, env(safe-area-inset-bottom))"
>
  <a href="#/overview" class="flex items-center gap-2.5 px-1 py-1 lg:px-2" aria-label="Pitaka, overview" onclick={tapLogo}>
    <img src="/icon.svg" alt="" class="size-10 shrink-0 rounded-[12px]" />
    <span class="title hidden text-xl lg:block">Pitaka</span>
  </a>
  <button class="btn btn-primary add-btn mt-5 !min-h-11 w-full !px-0" class:open={!!app.sheet} onclick={add} title="Add (N)">
    {#key burst}{#if burst}<span class="ripple" aria-hidden="true"></span>{/if}{/key}
    {@render plus()}<span class="hidden lg:inline">{word("add", "Add transaction")}</span><span class="sr-only lg:hidden">Add transaction</span>
  </button>
  <nav bind:this={rail} class="relative mt-5 space-y-1" aria-label="Main">
    {#if railPill}<span class="nav-pill absolute inset-x-0 rounded-2xl bg-primary" style="top:{railPill.top}px; height:{railPill.h}px" aria-hidden="true"></span>{/if}
    {#each nav as [id, plainLabel, path]}
      <a
        href="#/{id}"
        class="nav-item relative flex items-center justify-center gap-3 rounded-2xl px-3 py-2.5 font-medium transition-colors duration-300 lg:justify-start {app.view === id ? 'text-on-primary' : 'text-ink-2 hover:bg-inset hover:text-ink'}"
        aria-current={app.view === id ? "page" : undefined}
        title={label(id, plainLabel)}
      >
        {@render icon(path)}<span class="hidden lg:inline">{label(id, plainLabel)}</span>
      </a>
    {/each}
  </nav>
  {#if app.skin === "anime"}
    <div class="mt-auto flex justify-center pb-3"><span class="lg:hidden"><Mascot size={46} /></span><span class="hidden lg:inline"><Mascot size={76} /></span></div>
  {/if}
  <div class="{app.skin === 'anime' ? '' : 'mt-auto'} hidden rounded-2xl bg-inset p-3.5 lg:block">
    <p class="text-xs font-medium text-muted">{word("netWorthShort", "Net worth")}</p>
    <p class="display mt-0.5 text-xl"><Money value={app.meta?.netWorth ?? 0} /></p>
  </div>
  <!-- Who's signed in, and the way out. -->
  <div class="mt-3 flex flex-col items-center gap-2 lg:flex-row lg:gap-2.5 lg:px-1">
    <a href="#/settings" class="rounded-full" title="Signed in as {app.user.username}"><Avatar size={36} /></a>
    <span class="hidden min-w-0 flex-1 truncate text-sm font-semibold lg:block">{app.user.username}</span>
    <button class="grid size-9 place-items-center rounded-full text-ink-2 hover:bg-inset hover:text-ink" onclick={signOut} title="Sign out" aria-label="Sign out">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H3" /></svg>
    </button>
  </div>
</aside>

<div class="md:pl-[92px] lg:pl-[252px]">
  <main class="mx-auto min-h-dvh max-w-[1240px] px-4 pb-36 sm:px-6 md:pb-10 lg:px-8" style="padding-top: max(1rem, env(safe-area-inset-top))">
    <!-- Large title, like the system apps; the month control sits beside it on monthly pages. -->
    <header class="flex flex-wrap items-center justify-between max-md:[&>div:last-child]:w-full gap-x-4 gap-y-3 pb-5 pt-2 md:pt-4">
      <div class="flex items-center gap-3">
        <button class="md:hidden" onclick={tapLogo} aria-label="Pitaka"><img src="/icon.svg" alt="" class="size-9 rounded-[11px]" /></button>
        <h1 class="display page-title text-[1.9rem] md:text-[2.3rem]">{label(app.view, nav.find((n) => n[0] === app.view)?.[1])}</h1>
      </div>
      {#if app.skin === "anime"}<span class="ml-auto md:hidden"><Mascot size={42} bubble="below" /></span>{/if}
      <div class="flex items-center gap-3">
        {#if monthly}<MonthSwitch />{/if}
      </div>
    </header>

    {#if app.error && !app.meta}
      <div class="panel p-6" role="alert">
        <p class="title text-xl">Can't reach Money Manager.</p>
        <p class="mt-1 text-ink-2">{app.error}</p>
        <button class="btn btn-primary mt-4" onclick={loadMeta}>Try again</button>
      </div>
    {:else if app.meta}
      {#key app.view}
        {#if app.anime === "manga" && !reduced()}<div class="speedlines" aria-hidden="true"></div>{/if}
        <div in:enter>
          <View />
        </div>
      {/key}
    {/if}
  </main>
</div>

<!-- iPhone: a floating glass tab bar, with Add as its own glass button beside it. -->
<div class="fixed inset-x-3 z-30 flex items-center gap-2.5 md:hidden" style="bottom: max(0.75rem, env(safe-area-inset-bottom))">
  <nav bind:this={bar} class="glass-strong relative grid flex-1 grid-cols-4 rounded-full p-1.5" aria-label="Main">
    {#if barPill}<span class="nav-pill absolute inset-y-1.5 rounded-full bg-inset" style="left:{barPill.left}px; width:{barPill.w}px" aria-hidden="true"></span>{/if}
    {#each nav as [id, plainLabel, path]}
      <a
        href="#/{id}"
        class="nav-item relative flex flex-col items-center gap-0.5 rounded-full py-1.5 text-[10.5px] font-semibold transition-colors duration-300 {app.view === id ? 'text-ink' : 'text-muted'}"
        aria-current={app.view === id ? "page" : undefined}
      >
        {@render icon(path, 22)}{app.anime === "chuuni" ? word(id, short[id]) : short[id]}
      </a>
    {/each}
  </nav>
  <button class="btn btn-primary add-btn !size-[62px] !min-h-[62px] shrink-0 !p-0 shadow-xl" class:open={!!app.sheet} aria-label="Add transaction" onclick={add}>
    {#key burst}{#if burst}<span class="ripple" aria-hidden="true"></span>{/if}{/key}
    {@render plus(26)}
  </button>
</div>

{#key app.sheet}
  {#if !app.meta}
    <!-- forms need accounts and categories; a deep-linked sheet waits for them -->
  {:else if app.sheet?.mode === "tx"}
    <Sheet title={app.sheet.tx ? "Edit transaction" : "New transaction"} onclose={close}>
      <TxForm tx={app.sheet.tx} kind={app.sheet.kind} onclose={close} />
    </Sheet>
  {:else if app.sheet?.mode === "account"}
    <Sheet title={app.sheet.account ? `Edit ${app.sheet.account.name}` : "New account"} onclose={close}>
      <AccountForm account={app.sheet.account} onclose={close} />
    </Sheet>
  {/if}
{/key}

{/if}

<Toast />
