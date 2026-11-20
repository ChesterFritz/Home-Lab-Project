// Tiny synthesized sound effects (no audio files). Only play when the user turned sounds on.
let ctx;
function ac() { ctx ??= new (window.AudioContext || window.webkitAudioContext)(); return ctx; }

function tone(freq, start, len, type = "sine", gain = 0.08) {
  const a = ac(), o = a.createOscillator(), g = a.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, a.currentTime + start);
  g.gain.setValueAtTime(0, a.currentTime + start);
  g.gain.linearRampToValueAtTime(gain, a.currentTime + start + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + start + len);
  o.connect(g).connect(a.destination); o.start(a.currentTime + start); o.stop(a.currentTime + start + len + 0.02);
}

export const sfx = {
  sparkle() { [1568, 2093, 2637, 3136].forEach((f, i) => tone(f, i * 0.05, 0.25, "triangle", 0.05)); },
  boop() { const a = ac(), o = a.createOscillator(), g = a.createGain();
    o.type = "sine"; o.frequency.setValueAtTime(520, a.currentTime); o.frequency.exponentialRampToValueAtTime(1040, a.currentTime + 0.12);
    g.gain.setValueAtTime(0.09, a.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + 0.18);
    o.connect(g).connect(a.destination); o.start(); o.stop(a.currentTime + 0.2); },
  alarm() { [880, 660, 880, 660].forEach((f, i) => tone(f, i * 0.13, 0.12, "square", 0.04)); },
  // Viking: a low war horn that swells and bends up, and an anvil clang.
  horn() { const a = ac(), t = a.currentTime;
    [[110, .05], [165, .03], [220, .015]].forEach(([f, gain]) => {
      const o = a.createOscillator(), g = a.createGain(), lp = a.createBiquadFilter();
      o.type = "sawtooth"; o.frequency.setValueAtTime(f * .94, t); o.frequency.linearRampToValueAtTime(f, t + .25); o.frequency.setValueAtTime(f, t + 1.1); o.frequency.linearRampToValueAtTime(f * 1.06, t + 1.5);
      lp.type = "lowpass"; lp.frequency.setValueAtTime(400, t); lp.frequency.linearRampToValueAtTime(1400, t + .5);
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(gain, t + .3); g.gain.setValueAtTime(gain, t + 1.2); g.gain.exponentialRampToValueAtTime(.0001, t + 1.7);
      o.connect(lp).connect(g).connect(a.destination); o.start(t); o.stop(t + 1.75); }); },
  clang() { [[1180, .06], [1770, .035], [2950, .02], [530, .05]].forEach(([f, gain]) => tone(f, 0, .55, "triangle", gain)); },
  dark() { [220, 207.6, 174.6].forEach((f, i) => tone(f, i * 0.18, 0.5, "sawtooth", 0.03)); },
};
