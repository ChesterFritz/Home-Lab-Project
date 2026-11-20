<script>
  // Falling sakura petals (Kirino) or drifting black feathers and stars (Kuroneko). Canvas, ~30 sprites.
  import { onMount } from "svelte";
  let { flavor = "kirino", boost = 0 } = $props();
  let canvas;

  onMount(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const g = canvas.getContext("2d");
    let W, H, raf, items = [];
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const resize = () => { W = innerWidth; H = innerHeight; canvas.width = W * dpr; canvas.height = H * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0); };
    resize(); addEventListener("resize", resize);
    const spawn = (y) => ({
      x: Math.random() * W, y: y ?? -20, s: 6 + Math.random() * 9, r: Math.random() * 6.28,
      vr: (Math.random() - .5) * .05, vy: .5 + Math.random() * 1.1, vx: (Math.random() - .3) * .6,
      sway: Math.random() * 6.28, kind: Math.random() < .22 ? "star" : "main", hue: Math.random(),
    });
    const target = () => Math.round((W < 700 ? 18 : 32) * (1 + boost));
    for (let i = 0; i < target(); i++) items.push(spawn(Math.random() * H));

    const petal = (p) => {
      g.beginPath(); g.moveTo(0, -p.s);
      g.bezierCurveTo(p.s * .9, -p.s * .6, p.s * .7, p.s * .6, 0, p.s);
      g.bezierCurveTo(-p.s * .7, p.s * .6, -p.s * .9, -p.s * .6, 0, -p.s); g.closePath();
      g.fillStyle = p.hue < .5 ? "rgba(255,143,190,.85)" : p.hue < .8 ? "rgba(255,190,215,.9)" : "rgba(255,170,90,.75)"; g.fill();
      g.beginPath(); g.moveTo(0, -p.s * .9); g.lineTo(0, -p.s * .45); g.strokeStyle = "rgba(255,255,255,.7)"; g.lineWidth = 1.2; g.stroke();
    };
    const feather = (p) => {
      g.beginPath(); g.moveTo(0, -p.s * 1.3); g.quadraticCurveTo(p.s * .7, 0, 0, p.s * 1.3); g.quadraticCurveTo(-p.s * .5, 0, 0, -p.s * 1.3);
      g.fillStyle = p.hue < .7 ? "rgba(20,10,30,.8)" : "rgba(90,40,140,.75)"; g.fill();
      g.strokeStyle = "rgba(162,89,255,.55)"; g.lineWidth = 1; g.beginPath(); g.moveTo(0, -p.s * 1.2); g.lineTo(0, p.s * 1.2); g.stroke();
    };
    const star = (p) => {
      const r = p.s * .55; g.beginPath();
      for (let i = 0; i < 8; i++) { const a = (i * Math.PI) / 4, rr = i % 2 ? r * .35 : r; g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
      g.closePath(); g.fillStyle = flavor === "kuroneko" ? "rgba(200,160,255,.9)" : "rgba(255,255,255,.95)"; g.fill();
    };

    const tick = () => {
      g.clearRect(0, 0, W, H);
      while (items.length < target()) items.push(spawn());
      for (const p of items) {
        p.sway += .02; p.y += p.vy; p.x += p.vx + Math.sin(p.sway) * .6; p.r += p.vr;
        g.save(); g.translate(p.x, p.y); g.rotate(p.r);
        if (p.kind === "star") star(p); else (flavor === "kuroneko" ? feather : petal)(p);
        g.restore();
      }
      items = items.filter((p) => p.y < H + 30 && p.x > -40 && p.x < W + 40);
      raf = requestAnimationFrame(tick);
    };
    const vis = () => { cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(tick); };
    document.addEventListener("visibilitychange", vis);
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); removeEventListener("resize", resize); document.removeEventListener("visibilitychange", vis); };
  });
</script>

<canvas bind:this={canvas} class="pointer-events-none fixed inset-0 z-[5] h-full w-full" aria-hidden="true"></canvas>
