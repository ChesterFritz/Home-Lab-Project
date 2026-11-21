// One-shot visual effects for the anime style, drawn straight into <body> and cleaned up after.
import { animate } from "motion";
import { reduced } from "./motion.js";

const el = (html, css) => {
  const d = document.createElement("div");
  d.innerHTML = html;
  d.style.cssText = css;
  document.body.appendChild(d);
  return d;
};

const circleSvg = (size, color = "#d42a48", gold = "#e8c46a") => `
<svg viewBox="0 0 100 100" width="${size}" height="${size}" style="overflow:visible">
  <g style="transform-origin:50px 50px">
    <circle cx="50" cy="50" r="46" fill="none" stroke="${color}" stroke-width="1.2"/>
    <circle cx="50" cy="50" r="38" fill="none" stroke="${gold}" stroke-width=".7" stroke-dasharray="2 2"/>
    <polygon points="50,16 79.4,67 20.6,67" fill="none" stroke="${color}" stroke-width="1"/>
    <polygon points="50,84 20.6,33 79.4,33" fill="none" stroke="${color}" stroke-width="1"/>
    <circle cx="50" cy="50" r="12" fill="none" stroke="${gold}" stroke-width=".8"/>
  </g>
</svg>`;

/** Manga sound effect: a big inked word slams onto the page, then fades. */
export function stamp(text, x, y, size = 64) {
  if (reduced()) return;
  const d = el(
    `<span style="display:block;font-family:'Mochiy Pop One','Bangers',sans-serif;font-size:${size}px;line-height:1;color:#fff;
      -webkit-text-stroke:${Math.max(2, size / 18)}px #0a0a0a;paint-order:stroke fill;text-shadow:${size / 14}px ${size / 14}px 0 #0a0a0a;white-space:nowrap">${text}</span>`,
    `position:fixed;left:${x}px;top:${y}px;z-index:80;pointer-events:none;transform:translate(-50%,-50%)`
  );
  const inner = d.firstChild;
  const tilt = (Math.random() - 0.5) * 24;
  animate(inner, { scale: [2.4, 0.9, 1], rotate: [tilt * 2, tilt], opacity: [0, 1, 1] }, { duration: 0.32, ease: "easeOut" })
    .then(() => animate(inner, { opacity: [1, 0], y: [0, -16] }, { duration: 0.45, delay: 0.35 }))
    .then(() => d.remove());
}

/** Chuunibyou: a crimson summoning circle bursts open at a point and spins away. */
export function circleBurst(x, y, size = 220) {
  if (reduced()) return;
  const d = el(circleSvg(size), `position:fixed;left:${x - size / 2}px;top:${y - size / 2}px;z-index:80;pointer-events:none;filter:drop-shadow(0 0 8px #d42a48)`);
  animate(d.firstElementChild, { scale: [0.1, 1.15], rotate: [0, 200], opacity: [1, 0] }, { duration: 0.8, ease: [0.22, 1, 0.36, 1] }).then(() => d.remove());
}

/**
 * The unlock (or re-seal) cinematic. `swap` runs at the peak, while the screen is covered,
 * so the style change itself is hidden behind the effect.
 */
export async function awaken(mode, turningOn, swap) {
  if (reduced()) return swap();
  const W = innerWidth, H = innerHeight, big = Math.max(W, H) * 1.1;
  if (mode === "chuuni") {
    const title = turningOn ? "SEAL RELEASED" : "THE SEAL IS RESTORED";
    const sub = turningOn ? "The Dark Coin Lord awakens." : "…for now.";
    const d = el(
      `<div style="position:absolute;inset:0;background:radial-gradient(circle,#2a0614,#07040c 70%)"></div>
       <div class="c" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);filter:drop-shadow(0 0 14px #d42a48)">${circleSvg(Math.min(W, H) * 0.8)}</div>
       <div class="t" style="position:absolute;inset:0;display:grid;place-content:center;text-align:center;gap:10px">
         <div style="font-family:Cinzel,Georgia,serif;font-weight:700;letter-spacing:.14em;font-size:clamp(28px,6vw,64px);
           background:linear-gradient(180deg,#fff3cf,#e8c46a 55%,#d42a48);-webkit-background-clip:text;background-clip:text;color:transparent;
           filter:drop-shadow(3px 0 0 #00e5ff) drop-shadow(-3px 0 0 #ff2050)">${title}</div>
         <div style="font-family:Cinzel,Georgia,serif;color:#cdb8e0;letter-spacing:.1em;font-size:clamp(13px,2vw,18px)">${sub}</div>
       </div>`,
      "position:fixed;inset:0;z-index:90;pointer-events:none"
    );
    const circle = d.querySelector(".c svg"), text = d.querySelector(".t");
    await animate(d, { opacity: [0, 1] }, { duration: 0.35 });
    if (turningOn) swap();
    animate(circle, { scale: [0.2, 1], rotate: [0, 240] }, { duration: 1.6, ease: [0.22, 1, 0.36, 1] });
    await animate(text, { opacity: [0, 1, 1, 0.3, 1], x: [0, -6, 5, -2, 0], scale: [1.3, 1] }, { duration: 0.9 });
    await new Promise((r) => setTimeout(r, 700));
    if (!turningOn) swap();
    await animate(d, { opacity: [1, 0] }, { duration: 0.5 });
    d.remove();
  } else {
    const title = turningOn ? "MANGA MODE" : "~ FIN ~";
    const sfx = turningOn ? "ドドドド" : "パタン";
    const d = el(
      `<div style="position:absolute;inset:0;background:#fff"></div>
       <div class="l" style="position:absolute;left:calc(50% - ${big * 0.8}px);top:calc(50% - ${big * 0.8}px);width:${big * 1.6}px;height:${big * 1.6}px;
         background:repeating-conic-gradient(#0a0a0a 0 .8deg, transparent .8deg 5deg);
         -webkit-mask:radial-gradient(circle,transparent 18%,#000 45%);mask:radial-gradient(circle,transparent 18%,#000 45%)"></div>
       <div class="t" style="position:absolute;inset:0;display:grid;place-content:center;text-align:center">
         <div style="font-family:'Mochiy Pop One',sans-serif;font-size:clamp(40px,9vw,110px);color:#fff;-webkit-text-stroke:4px #0a0a0a;paint-order:stroke fill;
           text-shadow:6px 6px 0 #0a0a0a;transform:rotate(-6deg)">${sfx}</div>
         <div style="margin-top:10px;font-family:Bangers,sans-serif;font-size:clamp(28px,5vw,56px);letter-spacing:.06em;background:#0a0a0a;color:#fff;
           padding:.1em .6em;transform:skewX(-8deg);justify-self:center">${title}</div>
       </div>`,
      "position:fixed;inset:0;z-index:90;pointer-events:none"
    );
    const lines = d.querySelector(".l"), text = d.querySelector(".t");
    await animate(d, { opacity: [0, 1] }, { duration: 0.2 });
    if (turningOn) swap();
    animate(lines, { scale: [1.4, 1], rotate: [0, 6] }, { duration: 1.4, ease: "easeOut" });
    await animate(text, { scale: [2.2, 0.95, 1], opacity: [0, 1] }, { duration: 0.4, ease: "easeOut" });
    await new Promise((r) => setTimeout(r, 900));
    if (!turningOn) swap();
    await animate(d, { opacity: [1, 0] }, { duration: 0.4 });
    d.remove();
  }
}
