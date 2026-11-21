<script>
  // Frame for every chart: title, optional legend, and a table-view twin (the accessible reading).
  let { title, note = "", legend = [], table = null, children, actions, class: cls = "" } = $props();
  let showTable = $state(false);
</script>

<section class="panel flex h-full flex-col p-4 sm:p-5 {cls}">
  <header class="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
    <div class="min-w-0">
      <h2 class="title text-lg">{title}</h2>
      {#if note}<p class="text-sm text-muted">{note}</p>{/if}
    </div>
    <div class="flex items-center gap-2">
      {@render actions?.()}
      {#if table}
        <button class="chip !min-h-8 !text-[0.82rem]" aria-pressed={showTable} onclick={() => (showTable = !showTable)}>
          {showTable ? "Chart" : "Table"}
        </button>
      {/if}
    </div>
  </header>
  {#if legend.length > 1 && !showTable}
    <ul class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-2">
      {#each legend as l (l.label)}
        <li class="flex items-center gap-1.5"><span class="inline-block size-2.5 rounded-[3px]" style="background:{l.color}"></span>{l.label}</li>
      {/each}
    </ul>
  {/if}
  <div class="mt-3 flex-1">
    {#if showTable && table}
      <div class="max-h-80 overflow-auto rounded-xl border border-line">
        <table class="w-full text-sm num">
          <thead class="sticky top-0 bg-inset text-left text-ink-2">
            <tr>{#each table.columns as c, i}<th class="px-3 py-2 font-semibold {i ? 'text-right' : ''}">{c}</th>{/each}</tr>
          </thead>
          <tbody>
            {#each table.rows as r}
              <tr class="border-t border-line">{#each r as v, i}<td class="px-3 py-1.5 {i ? 'text-right' : ''}">{v}</td>{/each}</tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      {@render children()}
    {/if}
  </div>
</section>
