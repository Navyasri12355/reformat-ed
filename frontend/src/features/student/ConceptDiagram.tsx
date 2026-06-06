import { useCallback, useEffect, useId, useRef, useState } from "react";

let _mermaidReady: Promise<typeof import("mermaid").default> | null = null;

function getMermaid() {
  if (!_mermaidReady) {
    _mermaidReady = import("mermaid").then((m) => {
      m.default.initialize({
        startOnLoad: false,
        theme: "neutral",
        securityLevel: "loose",
        // Never inject Mermaid's "Syntax error" graphic into the page.
        suppressErrorRendering: true,
      });
      return m.default;
    });
  }
  return _mermaidReady;
}

/**
 * Interactive per-segment concept map from the backend's Mermaid `meta.diagram`.
 * Pan by dragging, zoom with the wheel or the +/- controls, and reset. Collapsible
 * so it never surprises the learner.
 */
export function ConceptDiagram({ code, defaultOpen = true }: { code?: string; defaultOpen?: boolean }) {
  const svgRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(defaultOpen);
  const [failed, setFailed] = useState(false);
  const reactId = useId().replace(/:/g, "");

  // Pan/zoom transform.
  const [view, setView] = useState({ scale: 1, x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!open || !code || !svgRef.current) return;
    let active = true;
    (async () => {
      try {
        const mermaid = await getMermaid();
        // Validate first — returns false (does not throw) on bad syntax.
        const ok = await mermaid.parse(code, { suppressErrors: true });
        if (!active) return;
        if (!ok) {
          setFailed(true);
          return;
        }
        const { svg } = await mermaid.render(`mmd-${reactId}`, code);
        if (active && svgRef.current) {
          svgRef.current.innerHTML = svg;
          const el = svgRef.current.querySelector("svg");
          if (el) {
            el.removeAttribute("width");
            el.removeAttribute("height");
            el.style.width = "100%";
            el.style.height = "auto";
          }
        }
      } catch {
        if (active) setFailed(true);
      }
    })();
    return () => {
      active = false;
    };
  }, [code, open, reactId]);

  const zoom = useCallback((factor: number) => {
    setView((v) => ({ ...v, scale: Math.min(4, Math.max(0.4, v.scale * factor)) }));
  }, []);

  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      zoom(e.deltaY < 0 ? 1.12 : 0.89);
    },
    [zoom],
  );

  const onPointerDown = (e: React.PointerEvent) => {
    drag.current = { x: e.clientX - view.x, y: e.clientY - view.y };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!drag.current) return;
    setView((v) => ({ ...v, x: e.clientX - drag.current!.x, y: e.clientY - drag.current!.y }));
  };
  const onPointerUp = () => {
    drag.current = null;
  };
  const reset = () => setView({ scale: 1, x: 0, y: 0 });

  if (!code) return null;

  return (
    <div className="concept-map">
      <div className="concept-bar">
        <button className="concept-toggle" onClick={() => setOpen((v) => !v)}>
          Concept map {open ? "▾" : "▸"}
        </button>
        {open && !failed && (
          <div className="concept-controls">
            <button className="btn btn-sm btn-ghost" title="Zoom out" onClick={() => zoom(0.83)}>－</button>
            <button className="btn btn-sm btn-ghost" title="Zoom in" onClick={() => zoom(1.2)}>＋</button>
            <button className="btn btn-sm btn-ghost" title="Reset" onClick={reset}>⟲</button>
            <span className="note">drag to pan · scroll to zoom</span>
          </div>
        )}
      </div>
      {open &&
        (failed ? (
          <p className="note">(diagram unavailable)</p>
        ) : (
          <div
            className="concept-viewport"
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
          >
            <div
              className="concept-svg"
              ref={svgRef}
              style={{
                transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})`,
                transformOrigin: "center center",
              }}
            />
          </div>
        ))}
    </div>
  );
}
