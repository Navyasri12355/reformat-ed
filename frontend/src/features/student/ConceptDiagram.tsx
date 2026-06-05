import { useEffect, useId, useRef, useState } from "react";

let _mermaidReady: Promise<typeof import("mermaid").default> | null = null;

/** Load + initialise Mermaid once, lazily (keeps it out of the main bundle). */
function getMermaid() {
  if (!_mermaidReady) {
    _mermaidReady = import("mermaid").then((m) => {
      m.default.initialize({ startOnLoad: false, theme: "neutral", securityLevel: "loose" });
      return m.default;
    });
  }
  return _mermaidReady;
}

/**
 * Renders a per-segment concept map from the backend's Mermaid `meta.diagram`.
 * Collapsible so it never surprises the learner (default open). Fails quietly to
 * a text note if rendering is unavailable.
 */
export function ConceptDiagram({ code, defaultOpen = true }: { code?: string; defaultOpen?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(defaultOpen);
  const [failed, setFailed] = useState(false);
  const reactId = useId().replace(/:/g, "");

  useEffect(() => {
    if (!open || !code || !ref.current) return;
    let active = true;
    getMermaid()
      .then((mermaid) => mermaid.render(`mmd-${reactId}`, code))
      .then(({ svg }) => {
        if (active && ref.current) ref.current.innerHTML = svg;
      })
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, [code, open, reactId]);

  if (!code) return null;

  return (
    <div className="concept-map">
      <button className="concept-toggle" onClick={() => setOpen((v) => !v)}>
        🗺️ Concept map {open ? "▾" : "▸"}
      </button>
      {open &&
        (failed ? (
          <p className="note">(diagram unavailable)</p>
        ) : (
          <div className="concept-svg" ref={ref} />
        ))}
    </div>
  );
}
