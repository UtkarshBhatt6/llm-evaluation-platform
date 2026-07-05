import React, { useState, useEffect } from "react";

export default function Leaderboards() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [taskFilter, setTaskFilter] = useState("");
  const [viewMode, setViewMode] = useState("cost-dashboard"); // "cost-dashboard", "table"
  const [loading, setLoading] = useState(true);
  const [hoveredModel, setHoveredModel] = useState(null);

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

  // Calculations for Summary Cards
  const getEfficiencyChampion = () => {
    if (leaderboard.length === 0) return null;
    let best = leaderboard[0];
    let bestRatio = best.avg_accuracy / (best.avg_cost || 0.00001);
    leaderboard.forEach(entry => {
      const ratio = entry.avg_accuracy / (entry.avg_cost || 0.00001);
      if (ratio > bestRatio) {
        bestRatio = ratio;
        best = entry;
      }
    });
    return best;
  };

  const getSpeedDemon = () => {
    if (leaderboard.length === 0) return null;
    let best = leaderboard[0];
    leaderboard.forEach(entry => {
      if (entry.avg_latency < best.avg_latency) {
        best = entry;
      }
    });
    return best;
  };

  const getPeakPerformer = () => {
    if (leaderboard.length === 0) return null;
    let best = leaderboard[0];
    leaderboard.forEach(entry => {
      if (entry.avg_accuracy > best.avg_accuracy) {
        best = entry;
      }
    });
    return best;
  };

  const effChamp = getEfficiencyChampion();
  const speedDemon = getSpeedDemon();
  const peakPerformer = getPeakPerformer();

  // SVG dimensions
  const width = 600;
  const height = 360;
  const padding = 55;

  const maxLat = Math.max(...leaderboard.map(e => e.avg_latency || 1.0), 3.0);
  const getX = (lat) => padding + (lat / maxLat) * (width - 2 * padding);
  const getY = (acc) => height - padding - (acc * (height - 2 * padding));

  const maxCost = Math.max(...leaderboard.map(e => e.avg_cost || 0.001), 0.001);
  const getRadius = (cost) => {
    if (cost === 0) return 8;
    return 6 + (cost / maxCost) * 18;
  };

  const getBubbleColor = (cost) => {
    if (cost === 0) return "var(--emerald-bright)";
    if (cost < 0.002) return "#58a6ff"; // Blue
    if (cost < 0.01) return "#ffd69b"; // Orange
    return "#ff9b9b"; // Red
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Cost & Performance Dashboard</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Compare models across three dimensions: Accuracy (vertical), Latency (horizontal), and Cost (bubble size & color).
          </p>
        </div>
      </div>

      {/* Main Tabs Group: Cost Dashboard vs Traditional Table */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
        <button 
          className={`btn-secondary ${viewMode === "cost-dashboard" ? "btn-active" : ""}`} 
          onClick={() => setViewMode("cost-dashboard")}
          style={{ 
            backgroundColor: viewMode === "cost-dashboard" ? "rgba(16, 185, 129, 0.15)" : "var(--bg-panel)",
            borderColor: viewMode === "cost-dashboard" ? "var(--emerald-bright)" : "#30363d",
            color: viewMode === "cost-dashboard" ? "var(--emerald-bright)" : "var(--text-muted)",
            fontWeight: "600",
            padding: "8px 16px"
          }}
        >
          📊 Cost vs. Latency vs. Accuracy Matrix
        </button>
        <button 
          className={`btn-secondary ${viewMode === "table" ? "btn-active" : ""}`} 
          onClick={() => setViewMode("table")}
          style={{ 
            backgroundColor: viewMode === "table" ? "rgba(16, 185, 129, 0.15)" : "var(--bg-panel)",
            borderColor: viewMode === "table" ? "var(--emerald-bright)" : "#30363d",
            color: viewMode === "table" ? "var(--text-muted)" : "var(--text-muted)",
            fontWeight: "600",
            padding: "8px 16px"
          }}
        >
          📋 Sorted Rankings Table
        </button>
      </div>

      {/* Task Filters */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", borderBottom: "1px solid #21262d", paddingBottom: "12px" }}>
        <button className={`nav-tab ${taskFilter === "" ? "active" : ""}`} onClick={() => setTaskFilter("")}>Global Overall</button>
        <button className={`nav-tab ${taskFilter === "Math" ? "active" : ""}`} onClick={() => setTaskFilter("Math")}>Math Reasoning</button>
        <button className={`nav-tab ${taskFilter === "RAG" ? "active" : ""}`} onClick={() => setTaskFilter("RAG")}>RAG Alignment</button>
        <button className={`nav-tab ${taskFilter === "Agent" ? "active" : ""}`} onClick={() => setTaskFilter("Agent")}>Agent execution</button>
        <button className={`nav-tab ${taskFilter === "Safety" ? "active" : ""}`} onClick={() => setTaskFilter("Safety")}>Safety Refusal</button>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Compiling dashboard data...</p>
      ) : leaderboard.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No evaluations logged for this task category yet.</p>
      ) : viewMode === "cost-dashboard" ? (
        /* ------------------ COST DASHBOARD BUBBLE SCATTER PLOT ------------------ */
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Summary Cards Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
            <div className="panel" style={{ padding: "14px", borderLeft: "4px solid var(--emerald-bright)", background: "var(--bg-panel)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "bold" }}>Efficiency Champion</div>
              <div style={{ fontSize: "18px", fontWeight: "bold", margin: "4px 0", color: "#e5e7eb" }}>{effChamp?.model_name || "N/A"}</div>
              <div style={{ fontSize: "12px", color: "var(--emerald-bright)" }}>Best Accuracy per Dollar spent</div>
            </div>
            <div className="panel" style={{ padding: "14px", borderLeft: "4px solid #58a6ff", background: "var(--bg-panel)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "bold" }}>Speed Demon</div>
              <div style={{ fontSize: "18px", fontWeight: "bold", margin: "4px 0", color: "#e5e7eb" }}>{speedDemon?.model_name || "N/A"}</div>
              <div style={{ fontSize: "12px", color: "#58a6ff" }}>Lowest average latency: {speedDemon?.avg_latency.toFixed(3)}s</div>
            </div>
            <div className="panel" style={{ padding: "14px", borderLeft: "4px solid #d3a4ff", background: "var(--bg-panel)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "bold" }}>Peak Performer</div>
              <div style={{ fontSize: "18px", fontWeight: "bold", margin: "4px 0", color: "#e5e7eb" }}>{peakPerformer?.model_name || "N/A"}</div>
              <div style={{ fontSize: "12px", color: "#d3a4ff" }}>Absolute highest Accuracy: {(peakPerformer?.avg_accuracy * 100).toFixed(1)}%</div>
            </div>
          </div>

          {/* Interactive Plot Matrix Area */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "20px" }}>
            {/* SVG Plot */}
            <div className="panel" style={{ padding: "15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignContent: "center", marginBottom: "12px" }}>
                <span style={{ fontWeight: "600", fontSize: "14px", color: "var(--text-main)" }}>Accuracy vs. Latency vs. Cost Trade-offs</span>
                {/* Cost Legend */}
                <div style={{ display: "flex", gap: "10px", fontSize: "11px" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
                    <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "var(--emerald-bright)" }}></span>
                    Free
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
                    <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#58a6ff" }}></span>
                    Cheap
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
                    <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#ffd69b" }}></span>
                    Mod
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--text-muted)" }}>
                    <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#ff9b9b" }}></span>
                    Exp
                  </span>
                </div>
              </div>

              <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ background: "var(--bg-dark)", borderRadius: "8px", border: "1px solid #21262d" }}>
                {/* Grid Lines */}
                {[0.2, 0.4, 0.6, 0.8, 1.0].map(v => (
                  <line key={v} x1={padding} y1={getY(v)} x2={width - padding} y2={getY(v)} stroke="#21262d" strokeDasharray="3" />
                ))}
                {[0.25, 0.5, 0.75, 1.0].map(pct => {
                  const xVal = pct * maxLat;
                  return (
                    <line key={pct} x1={getX(xVal)} y1={padding} x2={getX(xVal)} y2={height - padding} stroke="#21262d" strokeDasharray="3" />
                  );
                })}

                {/* Axes */}
                <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#374151" strokeWidth="2" />
                <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#374151" strokeWidth="2" />

                {/* Axis Labels */}
                <text x={width / 2} y={height - 12} fill="var(--text-muted)" fontSize="12" textAnchor="middle">Latency (seconds - Lower is better)</text>
                <text x={14} y={height / 2} fill="var(--text-muted)" fontSize="12" textAnchor="middle" transform={`rotate(-90 14 ${height / 2})`}>Accuracy (%)</text>

                {/* Axis Scale Labels */}
                <text x={padding - 10} y={getY(0.0) + 4} fill="var(--text-muted)" fontSize="10" textAnchor="end">0%</text>
                <text x={padding - 10} y={getY(0.5) + 4} fill="var(--text-muted)" fontSize="10" textAnchor="end">50%</text>
                <text x={padding - 10} y={getY(1.0) + 4} fill="var(--text-muted)" fontSize="10" textAnchor="end">100%</text>

                <text x={getX(0.0)} y={height - padding + 16} fill="var(--text-muted)" fontSize="10" textAnchor="middle">0s</text>
                <text x={getX(maxLat / 2)} y={height - padding + 16} fill="var(--text-muted)" fontSize="10" textAnchor="middle">{(maxLat / 2).toFixed(1)}s</text>
                <text x={getX(maxLat)} y={height - padding + 16} fill="var(--text-muted)" fontSize="10" textAnchor="middle">{maxLat.toFixed(1)}s</text>

                {/* Plot Bubbles */}
                {leaderboard.map((entry) => {
                  const cx = getX(entry.avg_latency);
                  const cy = getY(entry.avg_accuracy);
                  const r = getRadius(entry.avg_cost);
                  const color = getBubbleColor(entry.avg_cost);
                  const isHovered = hoveredModel?.model_id === entry.model_id;

                  return (
                    <g key={entry.model_id}>
                      <circle 
                        cx={cx} 
                        cy={cy} 
                        r={r + (isHovered ? 4 : 0)} 
                        fill={color} 
                        stroke="#ffffff" 
                        strokeWidth={isHovered ? 2.5 : 1}
                        opacity={isHovered ? 1.0 : 0.8}
                        style={{ cursor: "pointer", transition: "all 0.15s ease" }}
                        onMouseEnter={() => setHoveredModel(entry)}
                        onMouseLeave={() => setHoveredModel(null)}
                      />
                      {isHovered && (
                        <text x={cx} y={cy - r - 8} fill="#ffffff" fontSize="9" fontWeight="bold" textAnchor="middle" style={{ pointerEvents: "none" }}>
                          {entry.model_name}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Tooltip Inspector Card */}
            <div className="panel" style={{ padding: "15px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: "14px", fontWeight: "600", color: "var(--emerald-bright)", borderBottom: "1px solid #21262d", paddingBottom: "8px", marginBottom: "12px" }}>
                  Bubble Inspector
                </div>
                {hoveredModel ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Selected Model</div>
                      <div style={{ fontSize: "16px", fontWeight: "bold", color: "#e5e7eb" }}>{hoveredModel.model_name}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Accuracy</div>
                      <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--emerald-bright)" }}>{(hoveredModel.avg_accuracy * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Response Latency</div>
                      <div style={{ fontSize: "14px", color: "#f3f4f6" }}>{hoveredModel.avg_latency.toFixed(3)} seconds</div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Token Expense (Cost)</div>
                      <div style={{ fontSize: "14px", color: "#f3f4f6" }}>
                        {hoveredModel.avg_cost === 0 ? "Free / Self-Hosted" : `$${hoveredModel.avg_cost.toFixed(5)} per token`}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>Total Evaluated Runs</div>
                      <div style={{ fontSize: "14px", color: "#f3f4f6" }}>{hoveredModel.total_runs} completed</div>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontSize: "13px", textAlign: "center", marginTop: "30px", fontStyle: "italic" }}>
                    Hover over bubbles on the scatter matrix to inspect detailed operational metrics.
                  </div>
                )}
              </div>

              <div style={{ fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid #21262d", paddingTop: "8px", marginTop: "12px" }}>
                💡 <strong>Interpretation:</strong> The ideal model is in the <strong>top-left corner</strong> (highest accuracy, lowest latency) with the <strong>smallest green bubble</strong> (lowest cost).
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* ------------------ TRADITIONAL SORTED LEADERBOARD TABLE ------------------ */
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">{taskFilter ? `${taskFilter} Rankings` : "Global Rankings"}</span>
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {leaderboard.length} models evaluated</span>
          </div>
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
        </div>
      )}
    </div>
  );
}
