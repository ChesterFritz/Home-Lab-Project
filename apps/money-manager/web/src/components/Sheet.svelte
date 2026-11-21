<script>
  // Bottom sheet on phones, centered dialog on wide screens. Escape and the scrim close it.
  import { fly, fade } from "svelte/transition";
  import { cubicOut, backOut, quintOut } from "svelte/easing";
  import { prefersReducedMotion } from "svelte/motion";
  import { animate, stagger } from "motion";

  let { title, onclose, children } = $props();
  let panel = $state();
  const wide = typeof matchMedia !== "undefined" && matchMedia("(min-width: 768px)").matches;

  $effect(() => {
    const prev = document.activeElement;
    // Start in the first field (the amount, so the number pad opens), not on the Close button.
    (panel?.querySelector("input:not([type=hidden]), textarea, select") ?? panel?.querySelector("button"))?.focus({ preventScroll: true });
    document.body.style.overflow = "hidden";
    // The form's rows follow the sheet in, one after another.
    const rows = panel?.querySelector("[data-body]")?.firstElementChild?.children;
    if (rows?.length && !prefersReducedMotion.current)
      animate([...rows], { opacity: [0, 1], y: [14, 0] }, { duration: 0.4, delay: stagger(0.045, { startDelay: 0.12 }), ease: [0.22, 1, 0.36, 1] });
    return () => {
      document.body.style.overflow = "";
      prev?.focus?.({ preventScroll: true });
    };
  });
  const dur = () => (prefersReducedMotion.current ? 0 : 1);

  // Wide screens: the dialog scales up out of the glass with a slight overshoot.
  function pop(node) {
    return { duration: 340 * dur(), easing: backOut, css: (t, u) => `opacity:${Math.min(1, t * 1.6)}; transform: scale(${0.9 + 0.1 * t})` };
  }
  // Phones: pull the sheet down by its top; past 110px (or a quick flick) it closes.
  let drag = $state(0), start = $state(null), t0 = 0;
  function down(e) {
    if (wide || e.pointerType === "mouse" || panel.scrollTop > 0) return;
    start = e.clientY; t0 = performance.now();
  }
  function moveDrag(e) {
    if (start === null) return;
    drag = Math.max(0, e.clientY - start);
  }
  function up() {
    if (start === null) return;
    const fast = drag / (performance.now() - t0) > 0.6;
    start = null;
    if (drag > 110 || (fast && drag > 30)) onclose();
    else drag = 0;
  }
  const pick = (n) => (wide ? pop(n) : fly(n, { y: 520, duration: 480 * dur(), easing: quintOut, opacity: 1 }));
  const pickOut = (n) => (wide ? { duration: 160 * dur(), css: (t) => `opacity:${t}; transform: scale(${0.96 + 0.04 * t})` } : fly(n, { y: 520 , duration: 260 * dur(), easing: cubicOut, opacity: 1 }));
</script>

<svelte:window onkeydown={(e) => e.key === "Escape" && onclose()} />

<div class="fixed inset-0 z-40 bg-[var(--scrim)]" transition:fade|global={{ duration: 220 * dur() }} onclick={onclose} aria-hidden="true"></div>
<div
  bind:this={panel}
  role="dialog"
  tabindex="-1"
  aria-modal="true"
  aria-label={title}
  class="fixed z-50 inset-x-0 bottom-0 max-h-[92dvh] overflow-y-auto rounded-t-[30px] glass-strong sheet-bg
         md:inset-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[min(560px,92vw)] md:rounded-[30px]"
  style="padding-bottom: max(1.25rem, env(safe-area-inset-bottom)); {drag ? `transform: translateY(${drag}px)` : ''}; {start === null ? 'transition: transform .35s cubic-bezier(.34,1.4,.64,1)' : ''}"
  in:pick|global
  out:pickOut|global
  onpointerdown={down}
  onpointermove={moveDrag}
  onpointerup={up}
  onpointercancel={up}
>
  <div class="mx-auto mt-2.5 h-1.5 w-11 rounded-full bg-line-strong md:hidden" aria-hidden="true"></div>
  <header class="flex items-center justify-between px-5 pt-3 md:pt-5">
    <h2 class="title text-xl">{title}</h2>
    <button class="btn btn-quiet !size-10 !min-h-10 !p-0" onclick={onclose} aria-label="Close"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg></button>
  </header>
  <div class="px-5 pt-4" data-body>
    {@render children()}
  </div>
</div>
