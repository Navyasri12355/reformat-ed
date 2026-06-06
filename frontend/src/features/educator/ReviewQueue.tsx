import { useEffect, useState } from "react";
import { transformsApi } from "../../api";
import type { ReviewQueueItem } from "../../api/types";

export function ReviewQueue() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Record<string, string>>({});

  const refresh = async () => {
    setLoading(true);
    try {
      const q = await transformsApi.reviewQueue(1);
      setItems(q.items);
      setTotal(q.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const decide = async (id: string, action: "approve" | "reject") => {
    const edited = editing[id];
    await transformsApi.review(id, action, action === "approve" ? edited : undefined, action === "reject" ? "Rejected by educator" : undefined);
    setItems((prev) => prev.filter((it) => it.transformed_atom_id !== id));
    setTotal((t) => Math.max(0, t - 1));
  };

  if (loading) return <div className="center muted">Loading queue…</div>;

  return (
    <div>
      <div className="row-between">
        <h2>Review queue</h2>
        <span className="muted">{total} pending</span>
      </div>
      {items.length === 0 && <p className="muted">Nothing to review.</p>}
      {items.map((it) => (
        <div className="card review-item" key={it.transformed_atom_id}>
          <div className="review-cols">
            <div>
              <h5>Original</h5>
              <p className="muted">{it.atom_preview}…</p>
            </div>
            <div>
              <h5>
                Transformed <span className="format-badge sm">{it.output_format}</span>
              </h5>
              <textarea
                defaultValue={it.transform_preview}
                onChange={(e) => setEditing((m) => ({ ...m, [it.transformed_atom_id]: e.target.value }))}
              />
            </div>
          </div>
          <div className="row">
            <button className="btn btn-ghost" onClick={() => decide(it.transformed_atom_id, "reject")}>
              Reject
            </button>
            <button className="btn" onClick={() => decide(it.transformed_atom_id, "approve")}>
              Approve
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
