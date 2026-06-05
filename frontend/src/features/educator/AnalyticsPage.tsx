import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiClient } from "../../api/client";

interface Row {
  student_id: string;
  student_name: string;
  atom_id: string;
  sequence_index: number;
  output_format: string | null;
  completions: number;
  retries: number;
  exits: number;
  avg_time_ms: number | null;
}

export function AnalyticsPage() {
  const { documentId = "" } = useParams();
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get(`/analytics/${documentId}`)
      .then((r) => setRows(r.data))
      .finally(() => setLoading(false));
  }, [documentId]);

  if (loading) return <div className="center muted">Loading analytics…</div>;

  return (
    <div>
      <h2>Engagement analytics</h2>
      {rows.length === 0 && <p className="muted">No learning signals recorded yet.</p>}
      {rows.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Atom</th>
              <th>Format</th>
              <th>Completions</th>
              <th>Retries</th>
              <th>Exits</th>
              <th>Avg time</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const struggling = r.retries > r.completions || r.exits > 0;
              return (
                <tr key={i} className={struggling ? "row-warn" : ""}>
                  <td>{r.student_name}</td>
                  <td>#{r.sequence_index}</td>
                  <td>{r.output_format ?? "—"}</td>
                  <td>{r.completions}</td>
                  <td>{r.retries}</td>
                  <td>{r.exits}</td>
                  <td>{r.avg_time_ms ? `${Math.round(r.avg_time_ms / 1000)}s` : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
