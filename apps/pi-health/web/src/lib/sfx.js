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
  dark() { [220, 207.6, 174.6].forEach((f, i) => tone(f, i * 0.18, 0.5, "sawtooth", 0.03)); },
};
