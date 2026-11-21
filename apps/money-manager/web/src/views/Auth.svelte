<script>
  // Sign in / create account. One glass card over the ambient field; the two modes share it,
  // with a sliding pill between them, and the confirm field folding in for registration.
  import { fly, slide } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { animate } from "motion";
  import { signIn } from "../lib/store.svelte.js";
  import { reduced } from "../lib/motion.js";

  let mode = $state("login");
  let username = $state("");
  let password = $state("");
  let confirm = $state("");
  let show = $state(false);
  let busy = $state(false);
  let error = $state("");
  let card = $state();

  const registering = $derived(mode === "register");
  const copy = $derived(
    registering
      ? { title: "Start your own book.", note: "Your accounts and transactions stay private to you.", cta: "Create account" }
      : { title: "Welcome back.", note: "Sign in to your money book.", cta: "Sign in" }
  );

  function switchTo(m) {
    mode = m;
    error = "";
    confirm = "";
  }

  async function submit(e) {
    e.preventDefault();
    error = "";
    if (registering && password !== confirm) {
      error = "The two passwords don't match.";
    } else {
      busy = true;
      try {
        await signIn(mode, username.trim(), password);
        return;
      } catch (err) {
        error = err.message;
      } finally {
        busy = false;
      }
    }
    // A wrong answer shakes the card, the way a lock screen does.
    if (!reduced()) animate(card, { x: [0, -10, 9, -6, 4, 0] }, { duration: 0.45 });
  }
</script>

<main class="grid min-h-dvh place-items-center px-4 py-10" style="padding-top: max(2.5rem, env(safe-area-inset-top))">
  <div class="w-full max-w-[420px]" in:fly={{ y: 30, duration: reduced() ? 0 : 600, easing: cubicOut }}>
    <div class="mb-6 flex items-center justify-center gap-3">
      <img src="/icon.svg" alt="" class="size-12 rounded-[14px] shadow-lg" />
      <span class="display text-3xl">Pitaka</span>
    </div>

    <section bind:this={card} class="panel glass-strong p-6 sm:p-8" aria-labelledby="auth-title">
      <div class="relative grid grid-cols-2 rounded-full bg-inset p-1" role="tablist" aria-label="Sign in or create an account">
        <span
          class="nav-pill absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-full bg-primary"
          style="transform: translateX({registering ? '100%' : '0'}); transition: transform .5s cubic-bezier(.34,1.4,.64,1)"
          aria-hidden="true"
        ></span>
        {#each [["login", "Sign in"], ["register", "Create account"]] as [m, label]}
          <button
            type="button"
            role="tab"
            aria-selected={mode === m}
            class="relative z-10 rounded-full py-2 text-sm font-semibold transition-colors duration-300 {mode === m ? 'text-on-primary' : 'text-ink-2'}"
            onclick={() => switchTo(m)}>{label}</button
          >
        {/each}
      </div>

      <div class="mt-6 grid">
        {#key mode}
          <div class="col-start-1 row-start-1" in:fly={{ y: 10, duration: reduced() ? 0 : 320, delay: 80 }} out:fly={{ y: -8, duration: reduced() ? 0 : 160 }}>
            <h1 id="auth-title" class="display text-[1.75rem]">{copy.title}</h1>
            <p class="mt-1 text-ink-2">{copy.note}</p>
          </div>
        {/key}
      </div>

      <form class="mt-6 space-y-4" onsubmit={submit}>
        <label class="block">
          <span class="label">Username</span>
          <input class="field" bind:value={username} autocomplete="username" autocapitalize="none" spellcheck="false" required minlength="3" maxlength="32" />
        </label>
        <label class="block">
          <span class="label">Password</span>
          <span class="relative block">
            <input
              class="field !pr-16"
              type={show ? "text" : "password"}
              bind:value={password}
              autocomplete={registering ? "new-password" : "current-password"}
              required
              minlength={registering ? 8 : undefined}
            />
            <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 rounded-full px-2.5 py-1 text-sm font-semibold text-ink-2 hover:bg-inset" onclick={() => (show = !show)}>
              {show ? "Hide" : "Show"}
            </button>
          </span>
          {#if registering}<span class="mt-1 block text-[13px] text-muted">At least 8 characters.</span>{/if}
        </label>
        {#if registering}
          <label class="block" transition:slide={{ duration: reduced() ? 0 : 260 }}>
            <span class="label">Confirm password</span>
            <input class="field" type={show ? "text" : "password"} bind:value={confirm} autocomplete="new-password" required />
          </label>
        {/if}

        {#if error}
          <p class="rounded-xl bg-[color-mix(in_srgb,var(--danger)_12%,transparent)] px-3.5 py-2.5 text-sm font-medium text-danger" role="alert" transition:slide={{ duration: 200 }}>
            {error}
          </p>
        {/if}

        <button class="btn btn-primary !min-h-12 w-full text-base" disabled={busy}>
          {#if busy}
            <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9" stroke-linecap="round" /></svg>
            {registering ? "Creating your book…" : "Signing in…"}
          {:else}
            {copy.cta}
          {/if}
        </button>
      </form>
    </section>

    <p class="mt-5 text-center text-sm text-muted">
      {#if registering}Already have an account? <button class="font-semibold text-ink underline-offset-2 hover:underline" onclick={() => switchTo("login")}>Sign in</button>
      {:else}New here? <button class="font-semibold text-ink underline-offset-2 hover:underline" onclick={() => switchTo("register")}>Create an account</button>{/if}
    </p>
  </div>
</main>
