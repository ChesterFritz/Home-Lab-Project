<script>
  import { store } from "../lib/store.svelte.js";
  import { sfx } from "../lib/sfx.js";
  import Icon from "./Icon.svelte";
  import { GLYPH } from "../lib/anime.js";
  let open = $state(false);
  let root;
  const themes = [
    { id: "", label: "Match system", sw: "linear-gradient(135deg,#eef1f4 50%,#171b20 50%)" },
    { id: "light", label: "Light", sw: "#eef1f4" },
    { id: "dark", label: "Dark", sw: "#171b20" },
    { id: "kirino", label: "Kirino ♡", note: "Pink tsundere", sw: "linear-gradient(135deg,#ff4fa3,#ff9a3c)" },
    { id: "kuroneko", label: "Kuroneko ✦", note: "Gothic fallen angel", sw: "linear-gradient(135deg,#120d1a,#a259ff)" },
    { id: "viking", label: "Viking ⚔", note: "Dragons, runes & longships", sw: "linear-gradient(135deg,#0b141b 30%,#ff7a1a 70%,#ffd36a)" },
  ];
  $effect(() => {
    if (!open) return;
    const off = (e) => { if (!root.contains(e.target)) open = false; };
    const esc = (e) => e.key === "Escape" && (open = false);
    addEventListener("pointerdown", off); addEventListener("keydown", esc);
    return () => { removeEventListener("pointerdown", off); removeEventListener("keydown", esc); };
  });
  function pick(id) {
    store.setTheme(id); open = false;
    if (store.sfx) ({ kirino: sfx.sparkle, kuroneko: sfx.dark, viking: sfx.horn })[id]?.();
  }
</script>

<div class="relative" bind:this={root}>
  <button type="button" onclick={() => (open = !open)} aria-haspopup="menu" aria-expanded={open} aria-label="Choose theme"
    class="theme-btn grid size-9 place-items-center rounded-xl border border-line bg-panel text-ink-2 transition hover:text-ink active:scale-95">
    {#if store.anime}<span class="text-[17px] leading-none">{GLYPH[store.anime]}</span>{:else}<Icon name="moon" size={17} stroke={2} />{/if}
  </button>
  {#if open}
    <div role="menu" class="menu absolute right-0 z-50 mt-2 w-64 rounded-2xl border border-line bg-panel p-1.5 shadow-xl">
      {#each themes as t}
        <button type="button" role="menuitemradio" aria-checked={store.theme === t.id} onclick={() => pick(t.id)}
          class="flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left text-[14px] hover:bg-well {store.theme === t.id ? 'bg-well font-semibold' : ''}">
          <span class="size-6 shrink-0 rounded-full ring-1 ring-line" style="background:{t.sw}"></span>
          <span class="min-w-0 flex-1">{t.label}{#if t.note}<span class="block text-[12px] font-normal text-ink-3">{t.note}</span>{/if}</span>
          {#if store.theme === t.id}<Icon name="check" size={16} stroke={2.4} class="text-ink" />{/if}
        </button>
      {/each}
      <div class="my-1 h-px bg-line"></div>
      {#if store.anime}
        <button type="button" onclick={() => { open = false; store.artOpen = true; }}
          class="flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left text-[14px] hover:bg-well">
          <span class="grid size-6 shrink-0 place-items-center rounded-full bg-well text-[13px]">{GLYPH[store.anime]}</span>
          <span class="flex-1">Character pictures &amp; music…<span class="block text-[12px] text-ink-3">Add your own</span></span>
        </button>
      {/if}
      <label class="flex cursor-pointer items-center gap-3 rounded-xl px-2.5 py-2 text-[14px] hover:bg-well">
        <input type="checkbox" class="size-4 accent-[var(--c-brand)]" checked={store.sfx}
          onchange={(e) => { store.setSfx(e.currentTarget.checked); if (e.currentTarget.checked) sfx.boop(); }} />
        <span class="flex-1">Sound effects<span class="block text-[12px] text-ink-3">Anime themes only</span></span>
      </label>
      {#if store.anime}
        {@const hasSong = !!store.custom[`${store.anime}-music`]}
        <label class="flex cursor-pointer items-center gap-3 rounded-xl px-2.5 py-2 text-[14px] hover:bg-well">
          <input type="checkbox" class="size-4 accent-[var(--c-brand)]" checked={store.music} disabled={!hasSong}
            onchange={(e) => store.setMusic(e.currentTarget.checked)} />
          <span class="flex-1 {hasSong ? '' : 'text-ink-3'}">Music ♪<span class="block text-[12px] text-ink-3">{hasSong ? "Theme song" : "Add a song in Character pictures & music"}</span></span>
        </label>
      {/if}
    </div>
  {/if}
</div>
