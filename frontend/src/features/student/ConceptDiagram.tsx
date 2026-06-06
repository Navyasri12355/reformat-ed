import { useMemo, useState } from "react";
import type { SimulatorMeta } from "../../api/types";

function parseDiagramRoot(diagram?: string): string | null {
  if (!diagram) return null;
  const match = diagram.match(/(?:^|\n)\s*(?:TOPIC|N0|A0)\s*\[\s*"([^"]+)"\s*\]/);
  return match ? match[1] : null;
}

function parseDiagramLabels(diagram?: string): string[] {
  if (!diagram) return [];
  const matches = [...diagram.matchAll(/\[\s*"([^"]+)"\s*\]/g)];
  const labels = matches.map((m) => m[1].trim()).filter(Boolean);
  if (labels.length <= 1) return labels;
  return labels.slice(1, 5);
}

/**
 * HTML-only concept flow. Uses semantic div-based cards instead of Mermaid/SVG
 * so the learning visual is topic-grounded and fully styleable.
 */
export function ConceptDiagram({
  simulator,
  keywords,
  diagram,
  defaultOpen = true,
}: {
  simulator?: SimulatorMeta;
  keywords?: string[];
  diagram?: string;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  const nodes = useMemo(() => {
    const simulatorSteps = simulator?.steps?.filter(Boolean) ?? [];
    const keywordNodes = (keywords ?? simulator?.keywords ?? [])
      .filter(Boolean)
      .slice(0, 4);
    const diagramNodes = parseDiagramLabels(diagram);
    const rawItems = simulatorSteps.length
      ? simulatorSteps.slice(0, 4)
      : keywordNodes.length
      ? keywordNodes
      : diagramNodes;
    // Normalize each item into a concise label: take the first sentence or
    // truncate to ~120 chars so the concept map isn't filled with long prose.
    const items = rawItems.map((it) => {
      if (!it) return it;
      const s = String(it).trim();
      const firstSent = s.split(/(?<=[.!?])\s+/)[0];
      if (firstSent.length <= 120) return firstSent.replace(/\s+/g, " ");
      return firstSent.slice(0, 117).trim() + "...";
    });
    const titleFromKeywords = keywordNodes.length
      ? keywordNodes.slice(0, 2).map((k) => String(k).replace(/_/g, " ").replace(/\s+/g, " ").trim()).join(" · ")
      : null;
    const titleFromDiagram = parseDiagramRoot(diagram);
    return {
      title: simulator?.concept ?? titleFromKeywords ?? titleFromDiagram ?? "Main idea",
      items,
      chips: Array.from(new Set(keywordNodes)),
    };
  }, [keywords, simulator, diagram]);

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
