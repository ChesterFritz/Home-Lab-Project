<script>
  // Ranked spending by category. One series → one color; values are direct-labeled, so no tooltip needed.
  import { peso, splitEmoji } from "../lib/fmt.js";

  let { items = [], total = 0, color = "var(--out)", max = 8, onpick } = $props();
  let grown = $state(false);

  const rows = $derived.by(() => {
    if (items.length <= max) return items;
    const rest = items.slice(max - 1);
    return [...items.slice(0, max - 1), { id: "__other", name: `${rest.length} more categories`, amount: rest.reduce((s, x) => s + x.amount, 0), count: rest.reduce((s, x) => s + x.count, 0) }];
  });
  const top = $derived(Math.max(1, ...rows.map((r) => r.amount)));

  // Bars grow from zero once after mount, then follow data changes with a CSS transition.
  $effect(() => {
    const id = requestAnimationFrame(() => (grown = true));
    return () => cancelAnimationFrame(id);
  });
</script>

<ul class="space-y-1">
  {#each rows as r (r.id)}
    {@const [emoji, name] = splitEmoji(r.name)}
    {@const clickable = r.id !== "__other" && onpick}
    <li>
      <button
        class="group grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 rounded-xl px-2 py-1.5 text-left {clickable ? 'hover:bg-inset' : 'cursor-default'}"
        onclick={() => clickable && onpick(r)}
        tabindex={clickable ? 0 : -1}
        aria-label="{r.name}: {peso(r.amount)}, {Math.round((r.amount / (total || 1)) * 100)} percent{clickable ? '. Show transactions' : ''}"
      >
        <span class="flex min-w-0 items-center gap-2 text-[0.95rem]">
          {#if emoji}<span aria-hidden="true">{emoji}</span>{/if}
          <span class="truncate">{name}</span>
          <span class="text-sm text-muted">{r.count}×</span>
        </span>
        <span class="num text-right text-[0.95rem] font-semibold">{peso(r.amount)}</span>
        <span class="col-span-2 flex items-center gap-2">
          <span class="h-2 flex-1 overflow-hidden rounded-full bg-inset">
            <span
              class="block h-full rounded-full"
              style="width:{grown ? (r.amount / top) * 100 : 0}%; background:{color}; transition: width .7s cubic-bezier(.22,1,.36,1)"
            ></span>
          </span>
          <span class="num w-10 text-right text-xs text-muted">{Math.round((r.amount / (total || 1)) * 100)}%</span>
        </span>
      </button>
    </li>
  {/each}
</ul>
