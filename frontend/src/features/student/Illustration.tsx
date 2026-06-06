import type { SimulatorMeta } from "../../api/types";

/**
 * Topic-grounded HTML simulator card. This replaces generic decorative SVGs with
 * lightweight semantic visualisations derived from the lesson content.
 */
export function Illustration({
  simulator,
  size = 80,
}: {
  simulator?: SimulatorMeta;
  size?: number;
}) {
  if (!simulator) return null;

  const steps = simulator.steps?.slice(0, 4) ?? [];
  const keywords = simulator.keywords?.slice(0, 4) ?? [];

  return (
    <div
      className="sim-card"
      role="img"
      aria-label={simulator.title}
      style={{ minHeight: size }}
    >
      <div className="sim-head">
        <span className="sim-badge">HTML simulator</span>
        <strong>{simulator.title}</strong>
      </div>

      <div className={`sim-body sim-${simulator.type}`}>
        <div className="sim-focus">
          <div className="sim-focus-label">Main concept</div>
          <div className="sim-focus-value">{simulator.concept}</div>
        </div>

        <div className="sim-rail">
          {steps.map((step, i) => (
            <div className="sim-step" key={i}>
              <span className="sim-dot">{i + 1}</span>
              <span>{step}</span>
            </div>
          ))}
        </div>

        {keywords.length > 0 && (
          <div className="sim-keywords">
            {keywords.map((kw) => (
              <span className="sim-keyword" key={kw}>
                {kw}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
