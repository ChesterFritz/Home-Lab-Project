<script>
  // The signed-in person's photo, or their initial on the primary color when there's none.
  import { app } from "../lib/store.svelte.js";
  let { size = 36, class: cls = "" } = $props();
  const name = $derived(app.user?.username ?? "");
</script>

<span class="relative grid shrink-0 place-items-center overflow-hidden rounded-full bg-primary font-bold uppercase text-on-primary {cls}" style="width:{size}px;height:{size}px;font-size:{size * 0.42}px" aria-hidden="true">
  {#if app.user?.avatar}
    {#key app.user.avatar}
      <img src="/auth/avatar?v={app.user.avatar}" alt="" class="size-full object-cover" style="animation: avatar-in .45s cubic-bezier(.34,1.56,.64,1)" />
    {/key}
  {:else}
    {name[0] ?? ""}
  {/if}
</span>
