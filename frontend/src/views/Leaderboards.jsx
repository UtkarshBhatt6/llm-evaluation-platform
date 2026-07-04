import React, { useState, useEffect } from "react";

export default function Leaderboards() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [taskFilter, setTaskFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const url = taskFilter 
        ? `http://localhost:8000/api/leaderboard?task=${taskFilter}`
        : "http://localhost:8000/api/leaderboard";
      const res = await fetch(url);
      const data = await res.json();
      setLeaderboard(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load leaderboard:", err);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, [taskFilter]);

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Evaluation Leaderboard</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Compare model performance rankings based on accuracy, cost, and response latency.
          </p>
        </div>
      </div>

      {/* Task Filters */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", borderBottom: "1px solid #21262d", paddingBottom: "12px" }}>
        <button className={`nav-tab ${taskFilter === "" ? "active" : ""}`} onClick={() => setTaskFilter("")}>Global Overall</button>
        <button className={`nav-tab ${taskFilter === "Math" ? "active" : ""}`} onClick={() => setTaskFilter("Math")}>Math Reasoning</button>
        <button className={`nav-tab ${taskFilter === "RAG" ? "active" : ""}`} onClick={() => setTaskFilter("RAG")}>RAG Alignment</button>
        <button className={`nav-tab ${taskFilter === "Agent" ? "active" : ""}`} onClick={() => setTaskFilter("Agent")}>Agent execution</button>
        <button className={`nav-tab ${taskFilter === "Safety" ? "active" : ""}`} onClick={() => setTaskFilter("Safety")}>Safety Refusal</button>
      </div>

      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">{taskFilter ? `${taskFilter} Rankings` : "Global Rankings"}</span>
          <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {leaderboard.length} models evaluated</span>
        </div>
        
        {loading ? (
          <p style={{ color: "var(--text-muted)" }}>Compiling rankings...</p>
        ) : leaderboard.length === 0 ? (
          <p style={{ color: "var(--text-muted)" }}>No evaluations logged for this task category yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: "8%" }}>Rank</th>
                <th>Model</th>
                <th>Provider</th>
                <th>Avg Accuracy / Success</th>
                <th>Avg Judge Score</th>
                <th>Avg Latency</th>
                <th>Avg Cost / Run</th>
                <th>Total Runs</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, index) => {
                const isCrown = index === 0;
                return (
                  <tr key={entry.model_id}>
                    <td className="strong" style={{ color: isCrown ? "gold" : "var(--text-main)", fontSize: "15px" }}>
                      {isCrown ? "👑 1" : `# ${index + 1}`}
                    </td>
                    <td className="strong">{entry.model_name}</td>
                    <td>
                      <span className="badge badge-completed" style={{ background: "rgba(52, 211, 153, 0.08)", color: "#58a6ff" }}>
                        {entry.provider}
                      </span>
                    </td>
                    <td className="strong" style={{ color: "var(--emerald-bright)" }}>
                      {(entry.avg_accuracy * 100).toFixed(1)}%
                    </td>
                    <td>{entry.avg_judge_score ? `${entry.avg_judge_score.toFixed(1)} / 10` : "N/A"}</td>
                    <td>{entry.avg_latency.toFixed(3)}s</td>
                    <td>
                      {entry.avg_cost === 0 ? (
                        <span style={{ color: "var(--emerald-bright)", fontSize: "12px" }}>Free (Local)</span>
                      ) : (
                        `$${entry.avg_cost.toFixed(4)}`
                      )}
                    </td>
                    <td style={{ color: "var(--text-muted)" }}>{entry.total_runs} runs</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
