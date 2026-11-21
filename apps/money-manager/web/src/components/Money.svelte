<script>
  // A peso figure that counts to its new value when it changes (e.g. switching months).
  import { Tween, prefersReducedMotion } from "svelte/motion";
  import { cubicOut } from "svelte/easing";
  import { untrack } from "svelte";
  import { peso } from "../lib/fmt.js";

  let { value = 0, sign = false, whole = false, class: cls = "", from = 0 } = $props();
  const t = new Tween(untrack(() => from), { duration: 900, easing: cubicOut });
  $effect(() => {
    t.set(value, { duration: prefersReducedMotion.current ? 0 : 900 });
  });
</script>

<span class={cls} aria-label={peso(value, { sign, whole })}><span aria-hidden="true">{peso(t.current, { sign, whole })}</span></span>
