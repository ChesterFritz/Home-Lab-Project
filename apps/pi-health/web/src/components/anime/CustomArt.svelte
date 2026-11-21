<script>
  // Upload your own character pictures. They are stored on the Pi only.
  import { store } from "../../lib/store.svelte.js";
  import { GLYPH, NAME } from "../../lib/anime.js";
  let dialog;
  let busy = $state(""), error = $state("");
  const flavor = $derived(store.anime ?? "kirino");
  const name = $derived(NAME[flavor]);
  const slots = [
    { kind: "main", label: "Main picture", hint: "Shown on the status card. Also used for any mood you leave empty." },
    { kind: "happy", label: "When all is well", hint: "Optional" },
    { kind: "worried", label: "On a warning", hint: "Optional" },
    { kind: "angry", label: "On a serious alert", hint: "Optional" },
    { kind: "dizzy", label: "When the Pi is offline", hint: "Optional" },
    { kind: "sprite", label: "Corner character", hint: "Stands in the bottom corner of the page. A cut-out PNG with a transparent background works best." },
    { kind: "bg", label: "Page background", hint: "Fills the page behind the cards, softly tinted." },
    { kind: "music", label: "Theme music", hint: "An MP3 that loops quietly while this theme is on. Turn it off with Music ♪ in the theme menu." },
  ];
  $effect(() => { if (store.artOpen) dialog?.showModal(); else dialog?.close(); });

  async function choose(kind, e) {
    const file = e.currentTarget.files?.[0]; e.currentTarget.value = "";
    if (!file) return;
    error = ""; busy = kind;
    try { await store.uploadCustom(`${flavor}-${kind}`, file); }
    catch (err) { error = err.message; }
    busy = "";
  }
</script>

<dialog bind:this={dialog} onclose={() => (store.artOpen = false)} class="art-dialog m-auto w-[min(640px,calc(100vw-24px))] rounded-3xl border border-line bg-panel p-0 text-ink backdrop:bg-black/50 backdrop:backdrop-blur-sm">
  <div class="flex items-start gap-3 border-b border-line p-5">
    <div class="min-w-0 flex-1">
      <h2 class="heading text-[18px] font-semibold">{name} pictures &amp; music</h2>
      <p class="mt-1 text-[13px] text-ink-3">Use pictures you've saved yourself. They're stored on your Pi only, not in the app's code or your GitHub repo.</p>
    </div>
    <button type="button" class="grid size-9 shrink-0 place-items-center rounded-xl border border-line text-ink-2 hover:text-ink" onclick={() => (store.artOpen = false)} aria-label="Close">✕</button>
  </div>
  <ul class="max-h-[65vh] divide-y divide-line overflow-auto px-5">
    {#each slots as s}
      {@const url = store.custom[`${flavor}-${s.kind}`]}
      <li class="flex items-center gap-4 py-3.5">
        <div class="grid size-16 shrink-0 place-items-center overflow-hidden rounded-2xl bg-well ring-1 ring-line">
          {#if url && s.kind === "music"}<span class="text-[26px] text-ink">♪</span>{:else if url}<img src={url} alt="" class="size-full object-cover" />{:else}<span class="text-[22px] text-ink-3">{GLYPH[flavor]}</span>{/if}
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-[14.5px] font-semibold">{s.label}</div>
          <div class="text-[12.5px] text-ink-3">{s.hint}</div>
        </div>
        <div class="flex shrink-0 flex-col items-end gap-1.5 sm:flex-row sm:items-center">
          <label class="cursor-pointer rounded-xl bg-ink px-3 py-1.5 text-[13px] font-semibold whitespace-nowrap text-panel {busy === s.kind ? 'opacity-60' : ''}">
            {busy === s.kind ? "Uploading…" : url ? "Replace" : s.kind === "music" ? "Choose song" : "Choose picture"}
            <input type="file" accept={s.kind === "music" ? "audio/mpeg,.mp3" : "image/png,image/jpeg,image/webp,image/gif"} class="sr-only" disabled={!!busy} onchange={(e) => choose(s.kind, e)} />
          </label>
          {#if url}<button type="button" class="text-[13px] text-ink-3 underline underline-offset-2 hover:text-critical-ink" onclick={() => store.removeCustom(`${flavor}-${s.kind}`)}>Remove</button>{/if}
        </div>
      </li>
    {/each}
  </ul>
  <div class="border-t border-line px-5 py-3.5 text-[12.5px]">
    {#if error}<p class="font-semibold text-critical-ink" role="alert">{error}</p>
    {:else}<p class="text-ink-3">PNG, JPEG, WebP or GIF, up to 8 MB each. Animated GIFs work too. Music: MP3 up to 20 MB. Each theme (Kirino, Kuroneko, Viking) has its own set; switch theme to set another.</p>{/if}
  </div>
</dialog>
