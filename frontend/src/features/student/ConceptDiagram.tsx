import { useMemo, useState } from "react";
import type { SimulatorMeta } from "../../api/types";

/**
 * HTML-only concept flow. Uses semantic div-based cards instead of Mermaid/SVG
 * so the learning visual is topic-grounded and fully styleable.
 */
export function ConceptDiagram({
  simulator,
  keywords,
  defaultOpen = true,
}: {
  simulator?: SimulatorMeta;
  keywords?: string[];
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  const nodes = useMemo(() => {
    const simulatorSteps = simulator?.steps?.filter(Boolean) ?? [];
    const keywordNodes = (keywords ?? simulator?.keywords ?? [])
      .filter(Boolean)
      .slice(0, 4);
    return {
      title: simulator?.concept ?? "Main idea",
      items: simulatorSteps.length ? simulatorSteps.slice(0, 4) : keywordNodes,
      chips: keywordNodes,
    };
  }, [keywords, simulator]);

  if (!simulator && nodes.items.length === 0) return null;

  return (
    <div className="concept-map html-concept-map">
      <div className="concept-bar">
        <button className="concept-toggle" onClick={() => setOpen((v) => !v)}>
          Concept map {open ? "▾" : "▸"}
        </button>
        {open && (
          <span className="note">HTML concept flow · no SVG rendering</span>
        )}
      </div>

      {open && (
        <div className="concept-viewport html-concept-viewport">
          <div className="concept-html-wrap">
            <div className="concept-root-card">
              <div className="concept-root-label">Core concept</div>
              <div className="concept-root-value">{nodes.title}</div>
            </div>

            <div
              className="concept-branches"
              role="list"
              aria-label="Concept branches"
            >
              {nodes.items.map((item, index) => (
                <div
                  className="concept-branch"
                  role="listitem"
                  key={`${index}-${item}`}
                >
                  <div className="concept-connector" aria-hidden="true" />
                  <div className="concept-node-card">
                    <span className="concept-node-index">{index + 1}</span>
                    <span>{item}</span>
                  </div>
                </div>
              ))}
            </div>

            {nodes.chips.length > 0 && (
              <div className="concept-chip-row">
                {nodes.chips.map((chip) => (
                  <span className="concept-chip" key={chip}>
                    {chip}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
