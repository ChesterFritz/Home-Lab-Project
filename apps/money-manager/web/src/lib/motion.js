export const reduced = () =>
  typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;

// Svelte action: the element rises into place the first time it scrolls into view.
export function reveal(node) {
  if (reduced() || typeof IntersectionObserver === "undefined") return;
  node.setAttribute("data-reveal", "");
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) if (e.isIntersecting) { node.classList.add("shown"); io.disconnect(); }
    },
    { rootMargin: "0px 0px -8% 0px" }
  );
  io.observe(node);
  return { destroy: () => io.disconnect() };
}
