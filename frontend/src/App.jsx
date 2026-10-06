import { useEffect, useMemo, useState } from "react";
import { fetchJobs, createJob } from "./api";

function fitBand(score) {
  if (score >= 70) return "high";
  if (score >= 40) return "mid";
  return "low";
}

function StatusPill({ status }) {
  const label = {
    drafted: "Drafted",
    scored: "Scored",
    low_fit: "Low fit",
  }[status] || status;

  return <span className={`pill pill-${status}`}>{label}</span>;
}

function NewJobForm({ onSubmit, submitting, onError }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    if (!text.trim()) return;
    onSubmit(text)
      .then(() => {
        setText("");
        setOpen(false);
      })
      .catch((e) => {
        onError(e.message);
      });
  }

  if (!open) {
    return (
      <button className="btn-primary" onClick={() => setOpen(true)}>
        Add job posting
      </button>
    );
  }

  return (
    <form className="new-job-form" onSubmit={handleSubmit}>
      <textarea
        autoFocus
        placeholder="Paste the full job posting here"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={8}
      />

      <div className="form-actions">
        <button
          type="button"
          className="btn-ghost"
          onClick={() => setOpen(false)}
        >
          Cancel
        </button>

        <button type="submit" className="btn-ghost" disabled={submitting}>
          {submitting ? "Scoring..." : "Score this job"}
        </button>
      </div>
    </form>
  );
}

function SkillRow({ match }) {
  return (
    <div className={`skill-row skill-${match.status}`}>
      <span className="skill-status">{match.status}</span>
      <span className="skill-name">{match.requirement}</span>
      <span className="skill-category">{match.category}</span>

      {match.evidence && (
        <p className="skill-evidence">{match.evidence}</p>
      )}
    </div>
  );
}

function DetailPanel({ job, onClose }) {
  const [copied, setCopied] = useState(false);

  function copyDraft() {
    if (!job.outreach) return;
    navigator.clipboard.writeText(job.outreach.message);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const grouped = useMemo(() => {
    const matches = job.analysis?.skill_matches || [];
    return {
      technical: matches.filter((m) => m.category === "technical"),
      soft: matches.filter((m) => m.category === "soft"),
    };
  }, [job]);

  return (
    <aside className="detail-panel">
      <div className="detail-header">
        <div>
          <h2>{job.requirements.title}</h2>
          <p className="detail-sub">
            {job.requirements.company} · {job.requirements.location}
          </p>
        </div>

        <button className="btn-ghost" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="detail-score">
        <span className={`score-big band-${fitBand(job.fit_score)}`}>{job.fit_score}</span>
        <StatusPill status={job.status} />
      </div>

      <section>
        <h3>Technical requirements</h3>
        {grouped.technical.map((m, i) => (
          <SkillRow key={i} match={m} />
        ))}
      </section>

      {grouped.soft.length > 0 && (
        <section>
          <h3>Soft requirements (not scored)</h3>
          {grouped.soft.map((m, i) => (
            <SkillRow key={i} match={m} />
          ))}
        </section>
      )}

      <section>
        <h3>Outreach draft</h3>
        {job.outreach ? (
          <div className="outreach-box">
            <p className="outreach-subject">{job.outreach.subject}</p>
            <p className="outreach-message">{job.outreach.message}</p>
            <button className="btn-ghost" onClick={copyDraft}>
              {copied ? "Copied" : "Copy message"}
            </button>
          </div>
        ) : (
          <p className="empty-note">Fit was below threshold - no draft was written.</p>
        )}
      </section>
    </aside>
  );
}

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [sortKey, setSortKey] = useState("fit_score");
  const [sortDir, setSortDir] = useState("desc");

  function load() {
    setError(null);
    setLoading(true);

    return fetchJobs()
      .then(setJobs)
      .catch((e) => {
        setError(e.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    load();
  }, []);

  function handleNewJob(text) {
    setError(null);
    setSubmitting(true);

    return createJob(text)
      .then(() => load())
      .finally(() => {
        setSubmitting(false);
      });
  }

  function handleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === "desc" ? "asc" : "desc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sortedJobs = useMemo(() => {
    const copy = [...jobs];

    copy.sort((a, b) => {
      const first = a[sortKey] ?? "";
      const second = b[sortKey] ?? "";

      const firstValue =
        typeof first === "string" ? first.toLowerCase() : first;

      const secondValue =
        typeof second === "string" ? second.toLowerCase() : second;

      if (firstValue < secondValue) return sortDir === "asc" ? -1 : 1;    // if asc, returns -1 otherwise 1(desc)
      if (firstValue > secondValue) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return copy;
  }, [jobs, sortKey, sortDir]);

  const selectedJob = jobs.find((j) => j.id === selectedId);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Job Radar</h1>
        <NewJobForm
          onSubmit={handleNewJob}
          submitting={submitting}
          onError={(message) => setError(message)}
        />
      </header>

      {error && <p className="error-banner">{error}</p>}

      {loading ? (
        <p className="empty-note">Loading...</p>
      ) : sortedJobs.length === 0 ? (
        <p className="empty-note">No jobs scored yet. Paste a posting above to get started.</p>
      ) : (
        <table className="job-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("company")}>
                Company
                {sortKey === "company" && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
              <th onClick={() => handleSort("title")}>
                Title
                {sortKey === "title" && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
              <th onClick={() => handleSort("fit_score")}>
                Fit
                {sortKey === "fit_score" && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
              <th onClick={() => handleSort("status")}>
                Status
                {sortKey === "status" && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
            </tr>
          </thead>

          <tbody>
            {sortedJobs.map((job) => (
              <tr
                key={job.id}
                className={job.id === selectedId ? "row-selected" : ""}
                onClick={() => setSelectedId(job.id)}
              >
                <td>{job.company || "—"}</td>
                <td>{job.title}</td>
                <td>
                  <span className={`score-chip band-${fitBand(job.fit_score)}`}>{job.fit_score}</span>
                </td>
                <td>
                  <StatusPill status={job.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selectedJob && <DetailPanel job={selectedJob} onClose={() => setSelectedId(null)} />}
    </div>
  );
}