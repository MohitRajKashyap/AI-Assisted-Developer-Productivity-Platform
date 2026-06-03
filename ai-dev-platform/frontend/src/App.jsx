import { useState, useEffect, useCallback } from "react";

// ─── API Client ───────────────────────────────────────────────────────────────
const API_BASE = typeof window !== "undefined" && window.location.port === "5173"
  ? "http://localhost:8000"
  : "";

async function api(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.error(`API error ${path}:`, err);
    return null;
  }
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const icons = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  lab: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M9 3h6v11l3.5 7H5.5L9 14V3z"/><path d="M9 3h6"/><path d="M7 16h10"/>
    </svg>
  ),
  bug: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M12 2c-2.2 0-4 1.8-4 4v2H6l-2 2v2h2v1l-2 2v2h2c0 2.2 1.8 4 4 4s4-1.8 4-4h2v-2l-2-2v-1h2V8l-2-2h-2V6c0-2.2-1.8-4-4-4z"/>
    </svg>
  ),
  pr: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/>
      <path d="M6 8v8M9 6h5a2 2 0 012 2v8"/>
    </svg>
  ),
  error: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M12 9v4m0 4h.01M10.3 3.6L2.5 17.4A2 2 0 004.2 20h15.6a2 2 0 001.7-2.6L13.7 3.6a2 2 0 00-3.4 0z"/>
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 3v18h18"/><path d="M7 16l4-4 4 4 4-8"/>
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="12" cy="12" r="3"/><path d="M12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>
    </svg>
  ),
  send: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
    </svg>
  ),
  loader: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spin">
      <path d="M21 12a9 9 0 11-6.219-8.56"/>
    </svg>
  ),
  check: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  copy: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
    </svg>
  ),
};

// ─── Score Bar ────────────────────────────────────────────────────────────────
function ScoreBar({ value, max = 1, label, color }) {
  const pct = Math.round((value / max) * 100);
  const clr = color || (pct >= 70 ? "#22c55e" : pct >= 40 ? "#f59e0b" : "#ef4444");
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3, color: "#94a3b8" }}>
        <span>{label}</span>
        <span style={{ color: clr, fontWeight: 700 }}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div style={{ height: 5, background: "#1e293b", borderRadius: 999 }}>
        <div style={{ height: "100%", width: `${pct}%`, background: clr, borderRadius: 999, transition: "width 0.6s ease" }} />
      </div>
    </div>
  );
}

// ─── Strategy Badge ───────────────────────────────────────────────────────────
const STRATEGY_COLORS = {
  baseline: "#64748b",
  chain_of_thought: "#6366f1",
  few_shot: "#0ea5e9",
  negative_example: "#f43f5e",
  self_reflection: "#a855f7",
  context_window: "#10b981",
};

function StrategyBadge({ name }) {
  return (
    <span style={{
      background: STRATEGY_COLORS[name] + "22",
      color: STRATEGY_COLORS[name],
      border: `1px solid ${STRATEGY_COLORS[name]}44`,
      padding: "2px 10px",
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 600,
      fontFamily: "monospace",
    }}>
      {name.replace(/_/g, " ")}
    </span>
  );
}

// ─── Stat Card ────────────────────────────────────────────────────────────────
function StatCard({ label, value, unit, sub, accent }) {
  return (
    <div style={{
      background: "#0f172a",
      border: "1px solid #1e293b",
      borderRadius: 12,
      padding: "20px 24px",
      flex: 1,
      minWidth: 140,
    }}>
      <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 800, color: accent || "#f1f5f9", fontFamily: "monospace" }}>
        {value}<span style={{ fontSize: 14, fontWeight: 400, color: "#64748b", marginLeft: 4 }}>{unit}</span>
      </div>
      {sub && <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

// ─── Code Block ───────────────────────────────────────────────────────────────
function CodeBlock({ code, language = "python" }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div style={{ position: "relative", background: "#020817", border: "1px solid #1e293b", borderRadius: 8, marginTop: 8 }}>
      <button onClick={copy} style={{
        position: "absolute", right: 10, top: 10, background: "#1e293b",
        border: "none", color: "#94a3b8", borderRadius: 6, cursor: "pointer",
        padding: "4px 8px", display: "flex", alignItems: "center", gap: 4, fontSize: 11,
      }}>
        {copied ? <span style={{ width: 14, height: 14, color: "#22c55e" }}>{icons.check}</span> : <span style={{ width: 14, height: 14 }}>{icons.copy}</span>}
        {copied ? "Copied" : "Copy"}
      </button>
      <pre style={{ padding: "16px", margin: 0, fontSize: 12, color: "#e2e8f0", overflow: "auto", fontFamily: "'JetBrains Mono', 'Fira Code', monospace", lineHeight: 1.6 }}>
        {code}
      </pre>
    </div>
  );
}

// ─── Markdown Renderer (simple) ───────────────────────────────────────────────
function SimpleMarkdown({ text }) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div style={{ fontSize: 13, lineHeight: 1.7, color: "#cbd5e1" }}>
      {lines.map((line, i) => {
        if (line.startsWith("## ")) return <h3 key={i} style={{ color: "#f1f5f9", margin: "16px 0 6px", fontSize: 15, fontWeight: 700 }}>{line.slice(3)}</h3>;
        if (line.startsWith("# ")) return <h2 key={i} style={{ color: "#f1f5f9", margin: "20px 0 8px", fontSize: 18, fontWeight: 800 }}>{line.slice(2)}</h2>;
        if (line.startsWith("### ")) return <h4 key={i} style={{ color: "#e2e8f0", margin: "12px 0 4px", fontSize: 13, fontWeight: 700 }}>{line.slice(4)}</h4>;
        if (line.startsWith("- ") || line.startsWith("* ")) return <li key={i} style={{ marginLeft: 16, marginBottom: 4, color: "#94a3b8" }}>{line.slice(2)}</li>;
        if (line.startsWith("```")) return null;
        if (line.trim() === "") return <br key={i} />;
        // Bold
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={i} style={{ margin: "2px 0" }}>
            {parts.map((p, j) => j % 2 === 1 ? <strong key={j} style={{ color: "#f1f5f9" }}>{p}</strong> : p)}
          </p>
        );
      })}
    </div>
  );
}

// ─── Dashboard Page ───────────────────────────────────────────────────────────
function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/dashboard/stats").then(d => {
      setStats(d);
      setLoading(false);
    });
  }, []);

  if (loading) return <LoadingSpinner text="Loading dashboard..." />;
  if (!stats) return <EmptyState text="Failed to load dashboard stats" />;

  const strategies = Object.entries(stats.strategy_comparison || {});

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Platform overview and experiment insights" />

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard label="Experiments" value={stats.total_experiments} accent="#6366f1" />
        <StatCard label="Bug Reports" value={stats.total_bug_reports} accent="#f43f5e" />
        <StatCard label="PR Reviews" value={stats.total_pr_reviews} accent="#0ea5e9" />
        <StatCard label="Agent Runs" value={stats.total_agent_executions} accent="#10b981" />
        <StatCard label="Avg Accuracy" value={(stats.avg_accuracy_score * 100).toFixed(1)} unit="%" accent="#22c55e" />
        <StatCard label="Hallucination" value={(stats.avg_hallucination_rate * 100).toFixed(1)} unit="%" accent="#f59e0b" />
        <StatCard label="Total Cost" value={`$${stats.total_cost_usd?.toFixed(4)}`} accent="#a855f7" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        {/* Strategy Comparison */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 16 }}>Strategy Comparison</div>
          {strategies.length === 0 ? (
            <div style={{ color: "#475569", fontSize: 12 }}>Run experiments to see comparisons</div>
          ) : (
            strategies.sort((a, b) => b[1].avg_score - a[1].avg_score).map(([name, scores]) => (
              <div key={name} style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <StrategyBadge name={name} />
                  <span style={{ fontSize: 12, color: "#94a3b8", fontFamily: "monospace" }}>
                    {(scores.avg_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ height: 4, background: "#1e293b", borderRadius: 999 }}>
                  <div style={{
                    height: "100%",
                    width: `${scores.avg_score * 100}%`,
                    background: STRATEGY_COLORS[name] || "#6366f1",
                    borderRadius: 999,
                  }} />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Recent Experiments */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 16 }}>Recent Experiments</div>
          {stats.recent_experiments?.length === 0 ? (
            <div style={{ color: "#475569", fontSize: 12 }}>No experiments yet. Try the Prompt Lab!</div>
          ) : (
            stats.recent_experiments?.map(exp => (
              <div key={exp.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid #1e293b" }}>
                <div>
                  <div style={{ fontSize: 12, color: "#e2e8f0", marginBottom: 2 }}>{exp.task?.slice(0, 40)}...</div>
                  <div style={{ fontSize: 10, color: "#475569" }}>{new Date(exp.created_at).toLocaleDateString()}</div>
                </div>
                {exp.winner && <StrategyBadge name={exp.winner} />}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Best Strategy Banner */}
      {stats.best_strategy && (
        <div style={{
          background: "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
          borderRadius: 12, padding: "16px 24px",
          display: "flex", alignItems: "center", gap: 16,
        }}>
          <div style={{ fontSize: 24 }}>🏆</div>
          <div>
            <div style={{ fontSize: 11, color: "#c7d2fe", textTransform: "uppercase", letterSpacing: 1 }}>Best Performing Strategy</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#fff", fontFamily: "monospace" }}>
              {stats.best_strategy.replace(/_/g, " ").toUpperCase()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Prompt Lab Page ──────────────────────────────────────────────────────────
function PromptLabPage() {
  const [task, setTask] = useState("Review this Python function for bugs, security issues, and performance problems.");
  const [code, setCode] = useState(`def get_user_data(user_id):
    conn = db.connect("postgresql://admin:pass123@localhost/prod")
    query = "SELECT * FROM users WHERE id=" + user_id
    result = conn.execute(query)
    return result.fetchall()`);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selected, setSelected] = useState(null);

  const strategies = ["baseline", "chain_of_thought", "few_shot", "negative_example", "self_reflection", "context_window"];
  const [activeStrategies, setActiveStrategies] = useState(new Set(strategies));

  const toggleStrategy = (s) => {
    const next = new Set(activeStrategies);
    next.has(s) ? next.delete(s) : next.add(s);
    setActiveStrategies(next);
  };

  const runExperiment = async () => {
    if (!task.trim()) return;
    setLoading(true);
    setResults(null);
    const data = await api("/prompts/test", {
      method: "POST",
      body: JSON.stringify({
        task, code,
        strategies: Array.from(activeStrategies),
        model: "claude-sonnet-4-20250514",
      }),
    });
    setResults(data);
    if (data?.winner) setSelected(data.winner);
    setLoading(false);
  };

  const selectedResult = results?.results?.[selected];

  return (
    <div>
      <PageHeader title="Prompt Engineering Lab" subtitle="Compare 6 prompting strategies side-by-side" />

      {/* Input */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
        <label style={labelStyle}>Task Description</label>
        <textarea
          value={task}
          onChange={e => setTask(e.target.value)}
          rows={2}
          style={textareaStyle}
          placeholder="Describe the coding task..."
        />
        <label style={{ ...labelStyle, marginTop: 12 }}>Code to Analyze (optional)</label>
        <textarea
          value={code}
          onChange={e => setCode(e.target.value)}
          rows={6}
          style={{ ...textareaStyle, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}
          placeholder="Paste code here..."
        />
      </div>

      {/* Strategy Selection */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
        <label style={labelStyle}>Strategies to Test</label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          {strategies.map(s => (
            <button key={s} onClick={() => toggleStrategy(s)} style={{
              padding: "6px 14px", borderRadius: 999, fontSize: 11, fontWeight: 600, cursor: "pointer",
              fontFamily: "monospace",
              background: activeStrategies.has(s) ? STRATEGY_COLORS[s] + "22" : "#1e293b",
              color: activeStrategies.has(s) ? STRATEGY_COLORS[s] : "#64748b",
              border: `1px solid ${activeStrategies.has(s) ? STRATEGY_COLORS[s] + "88" : "#334155"}`,
            }}>
              {s.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={runExperiment}
        disabled={loading || activeStrategies.size === 0}
        style={primaryButtonStyle(loading)}
      >
        {loading ? (
          <><span style={{ width: 16, height: 16, display: "inline-block" }}>{icons.loader}</span> Running {activeStrategies.size} strategies...</>
        ) : (
          <><span style={{ width: 16, height: 16, display: "inline-block" }}>{icons.send}</span> Run Experiment</>
        )}
      </button>

      {/* Results */}
      {results && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9" }}>Results</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Winner:</div>
            <StrategyBadge name={results.winner} />
          </div>

          {/* Score Overview */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 8, marginBottom: 20 }}>
            {Object.entries(results.results || {}).sort((a, b) => b[1].overall_score - a[1].overall_score).map(([name, r]) => (
              <button key={name} onClick={() => setSelected(name)} style={{
                background: selected === name ? STRATEGY_COLORS[name] + "22" : "#0f172a",
                border: `1px solid ${selected === name ? STRATEGY_COLORS[name] : "#1e293b"}`,
                borderRadius: 10, padding: "12px 14px", cursor: "pointer", textAlign: "left",
              }}>
                <div style={{ fontSize: 10, color: STRATEGY_COLORS[name], fontFamily: "monospace", fontWeight: 700, marginBottom: 6 }}>
                  {name.replace(/_/g, " ")}
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: "#f1f5f9", fontFamily: "monospace" }}>
                  {(r.overall_score * 100).toFixed(0)}
                  <span style={{ fontSize: 11, color: "#475569" }}>%</span>
                </div>
                <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>
                  {r.latency_ms}ms · ${r.cost_usd.toFixed(5)}
                </div>
                {results.winner === name && (
                  <div style={{ fontSize: 9, color: "#22c55e", marginTop: 4, fontWeight: 700 }}>🏆 WINNER</div>
                )}
              </button>
            ))}
          </div>

          {/* Selected Detail */}
          {selectedResult && (
            <div style={{ background: "#0f172a", border: `1px solid ${STRATEGY_COLORS[selected]}44`, borderRadius: 12, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <StrategyBadge name={selected} />
                <div style={{ display: "flex", gap: 16, fontSize: 11, color: "#64748b" }}>
                  <span>{selectedResult.prompt_tokens + selectedResult.completion_tokens} tokens</span>
                  <span>{selectedResult.latency_ms}ms</span>
                  <span>${selectedResult.cost_usd.toFixed(5)}</span>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <div>
                  <ScoreBar value={selectedResult.correctness_score} label="Correctness" />
                  <ScoreBar value={selectedResult.relevance_score} label="Relevance" />
                  <ScoreBar value={selectedResult.completeness_score} label="Completeness" />
                </div>
                <div>
                  <ScoreBar value={selectedResult.consistency_score} label="Consistency" />
                  <ScoreBar value={1 - selectedResult.hallucination_score} label="No Hallucination" />
                  <ScoreBar value={selectedResult.overall_score} label="Overall" color="#6366f1" />
                </div>
              </div>

              <div style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, marginBottom: 6 }}>Model Output</div>
              <div style={{
                background: "#020817", border: "1px solid #1e293b", borderRadius: 8,
                padding: 16, maxHeight: 400, overflow: "auto",
              }}>
                <SimpleMarkdown text={selectedResult.output} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Bug Triage Page ──────────────────────────────────────────────────────────
function BugTriagePage() {
  const [form, setForm] = useState({
    title: "NullPointerException in UserService.getProfile()",
    description: "Production error occurring since deployment v2.4.1 on 2025-12-01. Users randomly get 500 errors when loading their profile page. Error rate is approximately 3% of all profile loads.",
    stack_trace: `java.lang.NullPointerException: Cannot invoke "String.length()" because "str" is null
    at com.example.UserService.getProfile(UserService.java:87)
    at com.example.ProfileController.show(ProfileController.java:42)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1067)`,
    code_snippet: `public UserProfile getProfile(String userId) {
    User user = userRepository.findById(userId);
    // TODO: add null check
    String formattedName = user.getDisplayName().toUpperCase();
    return new UserProfile(formattedName, user.getEmail());
}`,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [bugs, setBugs] = useState([]);
  const [view, setView] = useState("form"); // form | result | list

  useEffect(() => {
    api("/bugs/list").then(d => d && setBugs(d));
  }, []);

  const analyze = async () => {
    setLoading(true);
    const data = await api("/bugs/analyze", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setResult(data);
    setLoading(false);
    setView("result");
    api("/bugs/list").then(d => d && setBugs(d));
  };

  const severityColor = { critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#22c55e" };

  return (
    <div>
      <PageHeader title="Multi-Agent Bug Triage" subtitle="5-agent AI pipeline: Analyze → Classify → Root Cause → Fix → Report" />

      {/* Agent Flow Diagram */}
      <div style={{ display: "flex", gap: 4, alignItems: "center", marginBottom: 20, padding: "12px 16px", background: "#0f172a", borderRadius: 10, border: "1px solid #1e293b", overflowX: "auto" }}>
        {["Bug Report", "Analyzer", "Classifier", "Root Cause", "Fix Generator", "Report"].map((a, i, arr) => (
          <div key={a} style={{ display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
            <div style={{
              background: i === 0 ? "#1e293b" : i === arr.length - 1 ? "#1e293b" : "#6366f111",
              border: `1px solid ${i === 0 || i === arr.length - 1 ? "#334155" : "#6366f133"}`,
              color: i === 0 || i === arr.length - 1 ? "#64748b" : "#a5b4fc",
              borderRadius: 6, padding: "5px 10px", fontSize: 10, fontWeight: 600, whiteSpace: "nowrap",
            }}>{a}</div>
            {i < arr.length - 1 && <span style={{ color: "#334155", fontSize: 16 }}>→</span>}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["form", "result", "list"].map(v => (
          <button key={v} onClick={() => setView(v)} style={{
            padding: "6px 16px", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer",
            background: view === v ? "#6366f1" : "#1e293b",
            color: view === v ? "#fff" : "#64748b",
            border: `1px solid ${view === v ? "#6366f1" : "#334155"}`,
          }}>
            {v === "form" ? "New Bug" : v === "result" ? "Last Result" : `History (${bugs.length})`}
          </button>
        ))}
      </div>

      {view === "form" && (
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={{ gridColumn: "1 / -1" }}>
              <label style={labelStyle}>Bug Title *</label>
              <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} style={inputStyle} />
            </div>
            <div style={{ gridColumn: "1 / -1" }}>
              <label style={labelStyle}>Description *</label>
              <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={3} style={textareaStyle} />
            </div>
            <div>
              <label style={labelStyle}>Stack Trace</label>
              <textarea value={form.stack_trace} onChange={e => setForm({...form, stack_trace: e.target.value})} rows={5} style={{ ...textareaStyle, fontFamily: "monospace", fontSize: 11 }} />
            </div>
            <div>
              <label style={labelStyle}>Code Snippet</label>
              <textarea value={form.code_snippet} onChange={e => setForm({...form, code_snippet: e.target.value})} rows={5} style={{ ...textareaStyle, fontFamily: "monospace", fontSize: 11 }} />
            </div>
          </div>
          <button onClick={analyze} disabled={loading} style={{ ...primaryButtonStyle(loading), marginTop: 16 }}>
            {loading ? <><span style={{ width: 16, height: 16, display: "inline-block" }}>{icons.loader}</span> Running 5-Agent Pipeline...</> : "🤖 Analyze with AI Agents"}
          </button>
        </div>
      )}

      {view === "result" && result && (
        <div>
          {/* Summary */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
            <div style={{ background: severityColor[result.severity] + "22", border: `1px solid ${severityColor[result.severity]}44`, borderRadius: 10, padding: "12px 16px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 4 }}>SEVERITY</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: severityColor[result.severity] }}>{result.severity?.toUpperCase()}</div>
            </div>
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 16px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 4 }}>CATEGORY</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{result.category?.replace(/_/g, " ")}</div>
            </div>
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 16px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 4 }}>CONFIDENCE</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#22c55e" }}>{((result.confidence_score || 0) * 100).toFixed(0)}%</div>
            </div>
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 16px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 4 }}>DURATION</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{result.total_duration_ms}ms</div>
            </div>
          </div>

          {/* Agent Steps */}
          <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 12 }}>Agent Execution Trace</div>
            {result.agent_steps?.map((step, i) => (
              <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 12, marginBottom: 12, borderBottom: i < result.agent_steps.length - 1 ? "1px solid #1e293b" : "none" }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%",
                  background: "#6366f133", color: "#a5b4fc",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 800, flexShrink: 0,
                }}>{i + 1}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#a5b4fc", marginBottom: 2 }}>{step.agent}</div>
                  <div style={{ fontSize: 11, color: "#64748b" }}>→ {step.output_summary}</div>
                </div>
                <div style={{ fontSize: 10, color: "#475569", textAlign: "right", flexShrink: 0 }}>
                  <div>{step.duration_ms}ms</div>
                  <div>{step.tokens_used} tok</div>
                </div>
              </div>
            ))}
          </div>

          {/* Fix Suggestions */}
          {result.suggested_fixes?.length > 0 && (
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 12 }}>Suggested Fixes</div>
              {result.suggested_fixes.map((fix, i) => (
                <div key={i} style={{ background: "#020817", borderRadius: 8, padding: 14, marginBottom: 10 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#22c55e", marginBottom: 4 }}>{fix.approach}</div>
                  <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>{fix.description}</div>
                  {fix.code_diff && <CodeBlock code={fix.code_diff} />}
                  <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: 10, color: "#475569" }}>
                    <span>⏱ {fix.effort}</span>
                    <span>⚠️ Risk: {fix.risk}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Report */}
          <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 12 }}>Technical Report</div>
            <SimpleMarkdown text={result.report_markdown} />
          </div>
        </div>
      )}

      {view === "result" && !result && (
        <EmptyState text="No results yet. Run a bug analysis first." />
      )}

      {view === "list" && (
        <div>
          {bugs.length === 0 ? <EmptyState text="No bug reports yet" /> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {bugs.map(bug => (
                <div key={bug.id} style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{bug.title}</div>
                    <div style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>{new Date(bug.created_at).toLocaleString()}</div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {bug.severity && (
                      <span style={{ fontSize: 10, fontWeight: 700, color: severityColor[bug.severity], background: severityColor[bug.severity] + "22", padding: "2px 8px", borderRadius: 999 }}>
                        {bug.severity.toUpperCase()}
                      </span>
                    )}
                    <span style={{ fontSize: 10, color: "#64748b" }}>{bug.category || "unknown"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── PR Reviewer Page ─────────────────────────────────────────────────────────
function PRReviewerPage() {
  const [form, setForm] = useState({
    title: "feat: Add user authentication with JWT",
    description: "Implements JWT-based authentication. Adds login/logout endpoints and middleware.",
    author: "alice-dev",
    diff: `diff --git a/auth.py b/auth.py
+++ b/auth.py
@@ -0,0 +1,45 @@
+import jwt
+import sqlite3
+from datetime import datetime, timedelta
+
+SECRET_KEY = "mysecretkey123"  # TODO: move to env
+DB_PATH = "users.db"
+
+def authenticate(username, password):
+    conn = sqlite3.connect(DB_PATH)
+    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
+    user = conn.execute(query).fetchone()
+    if user:
+        token = jwt.encode({"user_id": user[0], "exp": datetime.utcnow() + timedelta(hours=24)}, SECRET_KEY)
+        return token
+    return None
+
+def verify_token(token):
+    try:
+        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
+        return data["user_id"]
+    except:
+        return None
+
+def get_all_users():
+    conn = sqlite3.connect(DB_PATH)
+    return conn.execute("SELECT * FROM users").fetchall()`,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const review = async () => {
    setLoading(true);
    const data = await api("/pr/review", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setResult(data);
    setLoading(false);
  };

  const verdictStyle = {
    APPROVE: { bg: "#22c55e22", color: "#22c55e", text: "✅ APPROVED" },
    REQUEST_CHANGES: { bg: "#ef444422", color: "#ef4444", text: "❌ CHANGES REQUIRED" },
    COMMENT: { bg: "#f59e0b22", color: "#f59e0b", text: "💬 NEEDS COMMENT" },
  };

  const severityColors = { error: "#ef4444", warning: "#f59e0b", suggestion: "#6366f1", praise: "#22c55e" };

  return (
    <div>
      <PageHeader title="AI Pull Request Reviewer" subtitle="Automated code review: bugs, security, performance, style" />

      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <label style={labelStyle}>PR Title</label>
            <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Author</label>
            <input value={form.author} onChange={e => setForm({...form, author: e.target.value})} style={inputStyle} />
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label style={labelStyle}>Description</label>
            <input value={form.description} onChange={e => setForm({...form, description: e.target.value})} style={inputStyle} />
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label style={labelStyle}>Git Diff</label>
            <textarea value={form.diff} onChange={e => setForm({...form, diff: e.target.value})} rows={12} style={{ ...textareaStyle, fontFamily: "monospace", fontSize: 11 }} />
          </div>
        </div>
        <button onClick={review} disabled={loading} style={{ ...primaryButtonStyle(loading), marginTop: 16 }}>
          {loading ? <><span style={{ width: 16, height: 16, display: "inline-block" }}>{icons.loader}</span> Reviewing...</> : "🔍 Review Pull Request"}
        </button>
      </div>

      {result && (
        <div>
          {/* Verdict */}
          <div style={{
            background: verdictStyle[result.overall_verdict]?.bg || "#1e293b",
            border: `1px solid ${verdictStyle[result.overall_verdict]?.color || "#334155"}44`,
            borderRadius: 12, padding: "16px 20px", marginBottom: 16,
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: verdictStyle[result.overall_verdict]?.color }}>
              {verdictStyle[result.overall_verdict]?.text}
            </div>
            <div style={{ fontSize: 28, fontWeight: 900, color: verdictStyle[result.overall_verdict]?.color, fontFamily: "monospace" }}>
              {result.score}/10
            </div>
          </div>

          {/* Issue Counts */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginBottom: 16 }}>
            {[
              { label: "🐛 Bugs", val: result.bugs_found, color: "#ef4444" },
              { label: "🔒 Security", val: result.security_issues, color: "#f97316" },
              { label: "⚡ Performance", val: result.performance_issues, color: "#f59e0b" },
              { label: "🎨 Style", val: result.style_issues, color: "#6366f1" },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ background: "#0f172a", border: `1px solid ${val > 0 ? color + "44" : "#1e293b"}`, borderRadius: 10, padding: "12px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 22, fontWeight: 800, color: val > 0 ? color : "#475569" }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Comments */}
          {result.comments?.length > 0 && (
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 12 }}>Review Comments</div>
              {result.comments.map((c, i) => (
                <div key={i} style={{
                  borderLeft: `3px solid ${severityColors[c.severity] || "#334155"}`,
                  paddingLeft: 12, marginBottom: 12,
                }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 4, alignItems: "center" }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: severityColors[c.severity], textTransform: "uppercase" }}>{c.severity}</span>
                    <span style={{ fontSize: 10, color: "#475569" }}>{c.file}{c.line ? `:${c.line}` : ""}</span>
                    <span style={{ fontSize: 10, color: "#475569", background: "#1e293b", padding: "1px 6px", borderRadius: 4 }}>{c.category}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#e2e8f0", marginBottom: c.suggestion ? 4 : 0 }}>{c.message}</div>
                  {c.suggestion && (
                    <div style={{ fontSize: 11, color: "#6366f1", background: "#6366f111", padding: "4px 8px", borderRadius: 4, marginTop: 4 }}>
                      💡 {c.suggestion}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Summary Markdown */}
          <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
            <SimpleMarkdown text={result.review_markdown} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Error Analyzer Page ──────────────────────────────────────────────────────
function ErrorAnalyzerPage() {
  const [form, setForm] = useState({
    error_message: "AttributeError: 'NoneType' object has no attribute 'email'",
    stack_trace: `Traceback (most recent call last):
  File "app/routes/user.py", line 45, in get_profile
    return {"email": user.email, "name": user.name}
  File "app/services/user_service.py", line 23, in get_user
    return db.query(User).filter(User.id == user_id).first()
AttributeError: 'NoneType' object has no attribute 'email'`,
    source_code: `def get_profile(user_id: str):
    user = user_service.get_user(user_id)
    return {"email": user.email, "name": user.name}`,
    language: "Python",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const analyze = async () => {
    setLoading(true);
    const data = await api("/errors/fix", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setResult(data);
    setLoading(false);
  };

  return (
    <div>
      <PageHeader title="Error-to-Fix Synthesis" subtitle="Chain-of-thought reasoning: Error → Root Cause → Fix" />

      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, padding: "10px 16px", background: "#0f172a", borderRadius: 8, border: "1px solid #1e293b" }}>
        {["Error Input", "→ Stage 1: Root Cause Analysis", "→ Stage 2: Fix Generation", "→ Output"].map((s, i) => (
          <span key={i} style={{ fontSize: 11, color: i === 0 || i === 3 ? "#64748b" : "#a5b4fc", fontFamily: "monospace" }}>{s}</span>
        ))}
      </div>

      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={labelStyle}>Error Message *</label>
            <input value={form.error_message} onChange={e => setForm({...form, error_message: e.target.value})} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Language</label>
            <select value={form.language} onChange={e => setForm({...form, language: e.target.value})} style={{ ...inputStyle, width: 120 }}>
              {["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++"].map(l => <option key={l}>{l}</option>)}
            </select>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <label style={labelStyle}>Stack Trace</label>
            <textarea value={form.stack_trace} onChange={e => setForm({...form, stack_trace: e.target.value})} rows={6} style={{ ...textareaStyle, fontFamily: "monospace", fontSize: 11 }} />
          </div>
          <div>
            <label style={labelStyle}>Source Code</label>
            <textarea value={form.source_code} onChange={e => setForm({...form, source_code: e.target.value})} rows={6} style={{ ...textareaStyle, fontFamily: "monospace", fontSize: 11 }} />
          </div>
        </div>
        <button onClick={analyze} disabled={loading} style={{ ...primaryButtonStyle(loading), marginTop: 16 }}>
          {loading ? <><span style={{ width: 16, height: 16, display: "inline-block" }}>{icons.loader}</span> Synthesizing fix...</> : "⚡ Synthesize Fix"}
        </button>
      </div>

      {result && (
        <div>
          {/* Confidence + Type */}
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 12, marginBottom: 16, alignItems: "center" }}>
            <div style={{ background: "#ef444422", border: "1px solid #ef444444", borderRadius: 10, padding: "12px 20px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 2 }}>ERROR TYPE</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#ef4444" }}>{result.error_type}</div>
            </div>
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 20px" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 2 }}>ROOT CAUSE</div>
              <div style={{ fontSize: 13, color: "#e2e8f0" }}>{result.root_cause}</div>
            </div>
            <div style={{ background: "#22c55e22", border: "1px solid #22c55e44", borderRadius: 10, padding: "12px 20px", textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 2 }}>CONFIDENCE</div>
              <div style={{ fontSize: 22, fontWeight: 900, color: "#22c55e" }}>{((result.confidence_score || 0) * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Reasoning Chain */}
          {result.reasoning_chain?.length > 0 && (
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f1f5f9", marginBottom: 10 }}>Reasoning Chain</div>
              {result.reasoning_chain.map((step, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8 }}>
                  <div style={{ fontSize: 11, color: "#6366f1", fontFamily: "monospace", minWidth: 60 }}>Step {i + 1}</div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>{step}</div>
                </div>
              ))}
            </div>
          )}

          {/* Fix */}
          <div style={{ background: "#0f172a", border: "1px solid #22c55e44", borderRadius: 12, padding: 20, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#22c55e", marginBottom: 8 }}>🔧 Suggested Fix</div>
            <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 10 }}>{result.fix_explanation}</div>
            <CodeBlock code={result.fix_code} />
          </div>

          {/* Prevention Tips */}
          {result.prevention_tips?.length > 0 && (
            <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f1f5f9", marginBottom: 10 }}>Prevention Tips</div>
              {result.prevention_tips.map((tip, i) => (
                <div key={i} style={{ fontSize: 12, color: "#94a3b8", marginBottom: 6, paddingLeft: 12, borderLeft: "2px solid #6366f133" }}>
                  {tip}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Experiment Tracker Page ──────────────────────────────────────────────────
function ExperimentTrackerPage() {
  const [history, setHistory] = useState([]);
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api("/evaluations/history?limit=50"),
      api("/evaluations/strategy-comparison"),
    ]).then(([hist, comp]) => {
      hist && setHistory(hist);
      comp && setComparison(comp);
      setLoading(false);
    });
  }, []);

  if (loading) return <LoadingSpinner text="Loading experiment data..." />;

  const metrics = ["avg_score", "avg_hallucination", "avg_cost", "avg_latency"];
  const metricLabels = { avg_score: "Avg Score", avg_hallucination: "Hallucination", avg_cost: "Cost (USD)", avg_latency: "Latency (ms)" };
  const metricColors = { avg_score: "#22c55e", avg_hallucination: "#ef4444", avg_cost: "#a855f7", avg_latency: "#f59e0b" };

  return (
    <div>
      <PageHeader title="Experiment Tracker" subtitle="Track prompt performance across runs and strategies" />

      {/* Strategy Comparison Table */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 16 }}>Strategy Comparison</div>
        {comparison.length === 0 ? (
          <EmptyState text="Run experiments to populate comparison data" />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Strategy</th>
                  <th style={thStyle}>Avg Score</th>
                  <th style={thStyle}>Hallucination</th>
                  <th style={thStyle}>Avg Cost</th>
                  <th style={thStyle}>Avg Latency</th>
                  <th style={thStyle}>Runs</th>
                </tr>
              </thead>
              <tbody>
                {comparison.sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0)).map(row => (
                  <tr key={row.strategy}>
                    <td style={tdStyle}><StrategyBadge name={row.strategy} /></td>
                    <td style={tdStyle}>
                      <span style={{ color: "#22c55e", fontFamily: "monospace", fontWeight: 700 }}>
                        {((row.avg_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ color: (row.avg_hallucination || 0) < 0.2 ? "#22c55e" : "#ef4444", fontFamily: "monospace" }}>
                        {((row.avg_hallucination || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td style={tdStyle}><span style={{ fontFamily: "monospace", color: "#a855f7" }}>${(row.avg_cost || 0).toFixed(5)}</span></td>
                    <td style={tdStyle}><span style={{ fontFamily: "monospace", color: "#f59e0b" }}>{Math.round(row.avg_latency || 0)}ms</span></td>
                    <td style={tdStyle}><span style={{ color: "#64748b" }}>{row.run_count}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Evaluations */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#f1f5f9", marginBottom: 16 }}>Recent Evaluations</div>
        {history.length === 0 ? (
          <EmptyState text="No evaluations yet" />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Strategy</th>
                  <th style={thStyle}>Score</th>
                  <th style={thStyle}>Hallucination</th>
                  <th style={thStyle}>Latency</th>
                  <th style={thStyle}>Cost</th>
                  <th style={thStyle}>Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map(row => (
                  <tr key={row.id}>
                    <td style={tdStyle}><StrategyBadge name={row.strategy} /></td>
                    <td style={tdStyle}>
                      <div style={{ width: 60 }}>
                        <div style={{ height: 3, background: "#1e293b", borderRadius: 999, marginBottom: 2 }}>
                          <div style={{ height: "100%", width: `${(row.overall_score || 0) * 100}%`, background: "#22c55e", borderRadius: 999 }} />
                        </div>
                        <span style={{ fontSize: 10, color: "#22c55e", fontFamily: "monospace" }}>{((row.overall_score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td style={tdStyle}><span style={{ fontSize: 11, fontFamily: "monospace", color: (row.hallucination_score || 0) < 0.2 ? "#22c55e" : "#f59e0b" }}>{((row.hallucination_score || 0) * 100).toFixed(0)}%</span></td>
                    <td style={tdStyle}><span style={{ fontSize: 11, fontFamily: "monospace", color: "#f59e0b" }}>{row.latency_ms}ms</span></td>
                    <td style={tdStyle}><span style={{ fontSize: 11, fontFamily: "monospace", color: "#a855f7" }}>${(row.cost_usd || 0).toFixed(5)}</span></td>
                    <td style={tdStyle}><span style={{ fontSize: 10, color: "#475569" }}>{new Date(row.created_at).toLocaleDateString()}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Settings Page ────────────────────────────────────────────────────────────
function SettingsPage() {
  const contextFiles = [
    { name: "project_overview.md", type: "overview", content: "# E-Commerce Platform\n\nMain product monorepo serving 2M+ users...\n\n## Stack\n- Backend: Python/FastAPI\n- Frontend: React/TypeScript\n- DB: PostgreSQL + Redis\n- Infra: Kubernetes on AWS" },
    { name: "architecture.md", type: "architecture", content: "# Architecture\n\n## Services\n- API Gateway (Kong)\n- User Service\n- Product Service\n- Order Service\n- Payment Service (PCI-compliant)\n\n## Data Flow\nAPI → Gateway → Service → DB" },
    { name: "coding_standards.md", type: "standards", content: "# Coding Standards\n\n- Type hints required\n- Black + isort for formatting\n- 80% test coverage minimum\n- No bare except clauses\n- Docstrings for all public APIs" },
    { name: "api_docs.md", type: "api_docs", content: "# API Documentation\n\n## Auth\nAll endpoints require Bearer JWT\n\n## Versioning\nAPI v2 at /api/v2/\n\n## Rate Limits\n1000 req/min per API key" },
    { name: "team_guidelines.md", type: "guidelines", content: "# Team Guidelines\n\n- PRs require 2 approvals\n- Deploy on Tuesdays/Thursdays only\n- Rollback within 15min of deploy issue\n- Postmortem for P0 incidents within 24h" },
  ];

  const [editing, setEditing] = useState(null);
  const [saved, setSaved] = useState(null);

  const save = async (file) => {
    const res = await api("/context", {
      method: "POST",
      body: JSON.stringify({ project_id: "demo-proj-1", ...file }),
    });
    if (res) {
      setSaved(file.filename);
      setTimeout(() => setSaved(null), 2000);
    }
  };

  return (
    <div>
      <PageHeader title="Context Management" subtitle="CLAUDE.md-inspired project context files loaded automatically by AI" />

      <div style={{ background: "#0f172a", border: "1px solid #6366f133", borderRadius: 12, padding: 16, marginBottom: 20, display: "flex", gap: 12, alignItems: "flex-start" }}>
        <div style={{ fontSize: 20 }}>📂</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#a5b4fc" }}>Project Context System</div>
          <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>These files are injected into the AI's context window before reasoning, similar to CLAUDE.md files and MCP configurations.</div>
          <code style={{ fontSize: 10, color: "#475569", marginTop: 8, display: "block" }}>context/ → project_overview.md · architecture.md · coding_standards.md · api_docs.md · team_guidelines.md</code>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
        {contextFiles.map(file => (
          <div key={file.name} style={{ background: "#0f172a", border: `1px solid ${editing?.name === file.name ? "#6366f1" : "#1e293b"}`, borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div>
                <code style={{ fontSize: 11, color: "#a5b4fc" }}>{file.name}</code>
                <div style={{ fontSize: 9, color: "#475569", textTransform: "uppercase", letterSpacing: 1, marginTop: 2 }}>{file.type}</div>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <button onClick={() => setEditing(editing?.name === file.name ? null : file)} style={{
                  fontSize: 10, padding: "3px 10px", borderRadius: 6, border: "1px solid #334155",
                  background: "#1e293b", color: "#94a3b8", cursor: "pointer",
                }}>
                  {editing?.name === file.name ? "Close" : "Edit"}
                </button>
                <button onClick={() => save(file)} style={{
                  fontSize: 10, padding: "3px 10px", borderRadius: 6, border: "1px solid #22c55e44",
                  background: saved === file.name ? "#22c55e22" : "#1e293b",
                  color: saved === file.name ? "#22c55e" : "#94a3b8", cursor: "pointer",
                }}>
                  {saved === file.name ? "✓ Saved" : "Save"}
                </button>
              </div>
            </div>
            {editing?.name === file.name ? (
              <textarea
                defaultValue={file.content}
                rows={8}
                style={{ ...textareaStyle, fontSize: 11, fontFamily: "monospace", width: "100%", boxSizing: "border-box" }}
              />
            ) : (
              <pre style={{ fontSize: 10, color: "#475569", margin: 0, overflow: "hidden", maxHeight: 80, fontFamily: "monospace", lineHeight: 1.5 }}>
                {file.content.slice(0, 200)}...
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Shared Components ────────────────────────────────────────────────────────
function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 900, color: "#f1f5f9", margin: 0, letterSpacing: -0.5 }}>{title}</h1>
      {subtitle && <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0 0" }}>{subtitle}</p>}
    </div>
  );
}

function LoadingSpinner({ text }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: 40, justifyContent: "center" }}>
      <span style={{ width: 20, height: 20, color: "#6366f1" }}>{icons.loader}</span>
      <span style={{ color: "#64748b", fontSize: 13 }}>{text || "Loading..."}</span>
    </div>
  );
}

function EmptyState({ text }) {
  return (
    <div style={{ textAlign: "center", padding: 40, color: "#475569", fontSize: 13 }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
      {text}
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const labelStyle = {
  fontSize: 11, fontWeight: 600, color: "#64748b",
  textTransform: "uppercase", letterSpacing: 0.5, display: "block", marginBottom: 6,
};

const inputStyle = {
  width: "100%", background: "#020817", border: "1px solid #1e293b", borderRadius: 8,
  padding: "10px 12px", color: "#e2e8f0", fontSize: 13, outline: "none",
  boxSizing: "border-box",
};

const textareaStyle = {
  ...inputStyle, resize: "vertical", fontFamily: "inherit", lineHeight: 1.5,
};

const primaryButtonStyle = (loading) => ({
  display: "flex", alignItems: "center", gap: 8, padding: "10px 20px",
  background: loading ? "#334155" : "#6366f1",
  color: loading ? "#64748b" : "#fff",
  border: "none", borderRadius: 8, fontSize: 13, fontWeight: 700,
  cursor: loading ? "not-allowed" : "pointer",
  transition: "background 0.2s",
});

const thStyle = {
  fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase",
  letterSpacing: 0.5, padding: "8px 12px", textAlign: "left",
  borderBottom: "1px solid #1e293b",
};

const tdStyle = {
  fontSize: 12, color: "#cbd5e1", padding: "10px 12px",
  borderBottom: "1px solid #0f172a",
};

// ─── CSS ──────────────────────────────────────────────────────────────────────
const globalCSS = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@400;600;700;800&display=swap');
  * { box-sizing: border-box; }
  body { margin: 0; background: #020817; font-family: 'Sora', sans-serif; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #020817; }
  ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { animation: spin 1s linear infinite; }
  select { appearance: none; }
  input:focus, textarea:focus, select:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px #6366f122;
  }
`;

// ─── Nav ──────────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "lab", label: "Prompt Lab", icon: "lab" },
  { id: "bugs", label: "Bug Triage", icon: "bug" },
  { id: "pr", label: "PR Review", icon: "pr" },
  { id: "errors", label: "Error Analyzer", icon: "error" },
  { id: "experiments", label: "Experiments", icon: "chart" },
  { id: "settings", label: "Context Files", icon: "settings" },
];

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("dashboard");

  const pages = {
    dashboard: <DashboardPage />,
    lab: <PromptLabPage />,
    bugs: <BugTriagePage />,
    pr: <PRReviewerPage />,
    errors: <ErrorAnalyzerPage />,
    experiments: <ExperimentTrackerPage />,
    settings: <SettingsPage />,
  };

  return (
    <>
      <style>{globalCSS}</style>
      <div style={{ display: "flex", minHeight: "100vh", background: "#020817" }}>
        {/* Sidebar */}
        <div style={{
          width: 220, background: "#050d1a", borderRight: "1px solid #0f172a",
          display: "flex", flexDirection: "column", padding: "20px 0", position: "fixed", height: "100vh", zIndex: 10,
        }}>
          {/* Logo */}
          <div style={{ padding: "0 20px 24px", borderBottom: "1px solid #0f172a" }}>
            <div style={{ fontSize: 11, color: "#6366f1", fontFamily: "'Space Mono', monospace", fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>AI DEV</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "#f1f5f9", lineHeight: 1.2 }}>Productivity<br/>Platform</div>
            <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
              <span style={{ fontSize: 9, color: "#475569", fontFamily: "monospace" }}>DEMO MODE</span>
            </div>
          </div>

          {/* Nav */}
          <nav style={{ padding: "12px 8px", flex: 1 }}>
            {NAV_ITEMS.map(item => (
              <button key={item.id} onClick={() => setPage(item.id)} style={{
                display: "flex", alignItems: "center", gap: 10, width: "100%",
                padding: "9px 12px", borderRadius: 8, marginBottom: 2,
                background: page === item.id ? "#6366f122" : "transparent",
                border: page === item.id ? "1px solid #6366f133" : "1px solid transparent",
                color: page === item.id ? "#a5b4fc" : "#475569",
                cursor: "pointer", textAlign: "left",
                transition: "all 0.15s",
              }}>
                <span style={{ width: 16, height: 16, flexShrink: 0 }}>{icons[item.icon]}</span>
                <span style={{ fontSize: 12, fontWeight: page === item.id ? 700 : 400 }}>{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Footer */}
          <div style={{ padding: "12px 20px", borderTop: "1px solid #0f172a" }}>
            <div style={{ fontSize: 9, color: "#1e293b", fontFamily: "monospace", textAlign: "center" }}>
              v1.0.0 · Portfolio Project
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main style={{ marginLeft: 220, flex: 1, padding: "28px 32px", maxWidth: "100%", overflow: "auto" }}>
          <div style={{ maxWidth: 1100 }}>
            {pages[page]}
          </div>
        </main>
      </div>
    </>
  );
}
