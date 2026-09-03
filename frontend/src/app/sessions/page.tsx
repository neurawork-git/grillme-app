"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

type PromptTemplate = {
  id: string;
  name: string;
  interview_focus: string;
  is_system: boolean;
};

type GrillSession = {
  id: string;
  format_id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
};

export default function SessionsPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [sessions, setSessions] = useState<GrillSession[]>([]);
  const [formatId, setFormatId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    const [templatesRes, sessionsRes] = await Promise.all([
      fetch("/api/prompt-templates"),
      fetch("/api/sessions"),
    ]);

    if (templatesRes.status === 401 || sessionsRes.status === 401) {
      router.push("/login");
      return;
    }

    const templatesData: PromptTemplate[] = await templatesRes.json();
    const sessionsData: GrillSession[] = await sessionsRes.json();
    setTemplates(templatesData);
    setSessions(sessionsData);
    if (templatesData.length > 0) setFormatId(templatesData[0].id);
    setLoading(false);
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const res = await fetch("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format_id: formatId }),
    });

    if (!res.ok) {
      setError("Session konnte nicht angelegt werden.");
      return;
    }

    await loadData();
  }

  if (loading) return <main style={{ maxWidth: 480, margin: "4rem auto" }}>Lädt…</main>;

  return (
    <main style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Meine Sessions</h1>

      {sessions.length === 0 ? (
        <p>Noch keine Sessions vorhanden.</p>
      ) : (
        <ul>
          {sessions.map((s) => (
            <li key={s.id}>
              {s.status} — {new Date(s.created_at).toLocaleString()}
            </li>
          ))}
        </ul>
      )}

      <h2>Neue Session</h2>
      <form onSubmit={handleCreate}>
        <label style={{ display: "block", marginBottom: 8 }}>
          Format
          <select
            value={formatId}
            onChange={(e) => setFormatId(e.target.value)}
            style={{ display: "block", width: "100%" }}
          >
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit">Session anlegen</button>
      </form>
    </main>
  );
}
