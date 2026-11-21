<script>
  // Manga paper: white page, a screentone gradient creeping in from two corners, and a faint
  // panel gutter grid, like the page under the panels.
</script>

<div class="pointer-events-none fixed inset-0 -z-10 bg-white" aria-hidden="true">
  <div class="absolute inset-0" style="background: radial-gradient(#0a0a0a 1px, transparent 1.4px) 0 0 / 7px 7px;
    mask: radial-gradient(ellipse 55% 45% at 100% 0%, #000, transparent 75%), radial-gradient(ellipse 50% 40% at 0% 100%, #000, transparent 75%);
    -webkit-mask: radial-gradient(ellipse 55% 45% at 100% 0%, #000, transparent 75%), radial-gradient(ellipse 50% 40% at 0% 100%, #000, transparent 75%);
    opacity: .22"></div>
  <!-- speed hatching along the left edge, like a motion panel -->
  <div class="absolute inset-y-0 left-0 w-24" style="background: repeating-linear-gradient(100deg, #0a0a0a 0 1px, transparent 1px 9px); opacity:.08;
    mask: linear-gradient(90deg, #000, transparent); -webkit-mask: linear-gradient(90deg, #000, transparent)"></div>
</div>
