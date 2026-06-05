import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { documentsApi } from "../../api";
import type { DocumentOut } from "../../api/types";

export function EducatorDashboard() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [uploading, setUploading] = useState(false);
  const [subject, setSubject] = useState("");
  const [grade, setGrade] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<number | null>(null);

  const refresh = () => documentsApi.list().then(setDocs).catch(() => setDocs([]));

  useEffect(() => {
    refresh();
    pollRef.current = window.setInterval(refresh, 3000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  const upload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await documentsApi.upload(file, subject || undefined, grade || undefined);
      if (fileRef.current) fileRef.current.value = "";
      setSubject("");
      setGrade("");
      await refresh();
    } catch (e: any) {
      alert(e?.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="row-between">
        <h2>Curriculum</h2>
        <Link className="btn btn-ghost" to="/educator/review">
          Review queue →
        </Link>
      </div>

      <div className="card upload-card">
        <h4>Upload a lesson</h4>
        <p className="muted">PDF, DOCX, PPTX or TXT. We'll break it into curriculum atoms automatically.</p>
        <input ref={fileRef} type="file" accept=".pdf,.docx,.pptx,.txt" />
        <div className="row">
          <input placeholder="Subject (optional)" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <input placeholder="Grade level (optional)" value={grade} onChange={(e) => setGrade(e.target.value)} />
        </div>
        <button className="btn" onClick={upload} disabled={uploading}>
          {uploading ? "Uploading…" : "Upload & ingest"}
        </button>
      </div>

      <div className="doc-grid">
        {docs.map((d) => (
          <div className="card doc-card" key={d.id}>
            <h4>{d.file_name}</h4>
            <p>
              <StatusPill status={d.parse_status} /> · {d.page_count ?? "—"} pages
            </p>
            <Link className="btn btn-sm btn-ghost" to={`/educator/analytics/${d.id}`}>
              View analytics
            </Link>
          </div>
        ))}
        {docs.length === 0 && <p className="muted">No documents yet — upload one above.</p>}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  return <span className={`pill pill-${status}`}>{status}</span>;
}
