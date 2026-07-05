import React, { useState, useEffect } from "react";

export default function FailureAnalysis({ runId, setRunId }) {
  const [runs, setRuns] = useState([]);
  const [activeRunId, setActiveRunId] = useState(runId || "");
  const [runDetail, setRunDetail] = useState(null);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedFailureItem, setSelectedFailureItem] = useState(null);

  // Fetch completed runs for the left sidebar
  const fetchCompletedRuns = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/results");
      const data = await res.json();
      const completed = data.filter(r => r.status === "completed" || r.status === "failed");
      setRuns(completed);
      setLoadingRuns(false);
      
      // Auto-select first run if none is set
      if (completed.length && !activeRunId) {
        setActiveRunId(completed[0].id);
      }
    } catch (err) {
      console.error("Failed to load runs for failure analysis:", err);
    }
  };

  // Fetch detail for selected run
  const fetchRunDetail = async (id) => {
    if (!id) return;
    setLoadingDetail(true);
    try {
      const res = await fetch(`http://localhost:8000/api/results/${id}`);
      const data = await res.json();
      setRunDetail(data);
      setSelectedFailureItem(null);
      setLoadingDetail(false);
    } catch (err) {
      console.error("Failed to load run details:", err);
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchCompletedRuns();
  }, []);

  useEffect(() => {
    if (activeRunId) {
      fetchRunDetail(activeRunId);
    }
  }, [activeRunId]);

  // Sync state if selected from parent Dashboard
  useEffect(() => {
    if (runId) {
      setActiveRunId(runId);
    }
  }, [runId]);

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Failure Diagnostic Center</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Inspect model failure patterns clustered by type (Math, Reasoning, formatting, safety).
          </p>
        </div>
      </div>

      <div className="split-layout">
        {/* Sidebar: List completed runs */}
        <div className="split-sidebar">
          <span className="form-label">Select Evaluation Run</span>
          {loadingRuns ? (
            <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Loading runs...</p>
          ) : runs.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>No completed runs available.</p>
          ) : (
            runs.map((run) => (
              <div 
                key={run.id}
                className={`sidebar-item ${activeRunId === run.id ? "active" : ""}`}
                onClick={() => {
                  setActiveRunId(run.id);
                  setRunId(run.id); // sync parent state
                }}
              >
                <strong style={{ display: "block", fontSize: "13px", color: "var(--text-main)" }}>
                  Experiment #{run.experiment_id}
                  {run.status === "failed" && (
                    <span style={{ color: "var(--danger-neon)", marginLeft: "6px", fontSize: "10px", fontWeight: "bold" }}>
                      (Failed)
                    </span>
                  )}
                </strong>
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Run ID: {run.id.slice(0, 8)}...</span>
              </div>
            ))
          )}
        </div>

        {/* Main Content Area: Failures breakdown */}
        <div>
          {loadingDetail ? (
            <div className="panel"><p style={{ color: "var(--text-muted)" }}>Analyzing run failures...</p></div>
          ) : !runDetail ? (
            <div className="panel"><p style={{ color: "var(--text-muted)" }}>Please select a run from the sidebar.</p></div>
          ) : (
            <div>
              {/* Failure summary card */}
              <div className="panel" style={{ padding: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <h3 style={{ color: "var(--emerald-bright)", fontSize: "16px", marginBottom: "4px" }}>
                      Run Overview: {runDetail.model.name}
                    </h3>
                    <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                      Dataset: <strong>{runDetail.dataset.name}</strong> • Total Failures: <strong>
                        {Object.values(runDetail.failures || {}).reduce((acc, list) => acc + list.length, 0)}
                      </strong>
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <span className="badge badge-completed">
                      Accuracy: {runDetail.metrics_summary?.accuracy !== undefined ? `${(runDetail.metrics_summary.accuracy * 100).toFixed(0)}%` : "N/A"}
                    </span>
                    <span className="badge badge-pending">
                      Avg Latency: {runDetail.metrics_summary?.avg_latency !== undefined ? `${runDetail.metrics_summary.avg_latency.toFixed(2)}s` : "N/A"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Error Message if run status is failed */}
              {runDetail.status === "failed" && (
                <div className="panel" style={{ borderLeft: "4px solid var(--danger-neon)", padding: "16px", marginBottom: "16px", backgroundColor: "rgba(248, 81, 73, 0.08)" }}>
                  <span style={{ fontSize: "14px", fontWeight: "600", color: "var(--danger-neon)", display: "block", marginBottom: "6px" }}>
                    ⚠️ Execution Run Failed (System Error)
                  </span>
                  <pre style={{ margin: 0, padding: "10px", backgroundColor: "var(--bg-dark)", border: "1px solid #21262d", borderRadius: "6px", color: "#f85149", fontSize: "12px", whiteSpace: "pre-wrap", fontFamily: "monospace", overflowX: "auto" }}>
                    {runDetail.error_message || "Execution failed due to runtime exception or network timeout."}
                  </pre>
                </div>
              )}

              {/* Grid showing failures breakdown */}
              {runDetail.status === "failed" ? (
                <div className="panel" style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                  No semantic diagnostics are available for this run since the execution worker failed before completing metrics aggregation.
                </div>
              ) : Object.keys(runDetail.failures || {}).length === 0 ? (
                <div className="panel">
                  <p style={{ color: "var(--emerald-bright)", fontWeight: "600" }}>
                    🎉 No failures! The model passed all tests with 100% accuracy.
                  </p>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                  {/* Left Column: Failure Categories and Items list */}
                  <div>
                    {Object.entries(runDetail.failures).map(([category, items]) => (
                      <div key={category} className="panel" style={{ padding: "16px", marginBottom: "16px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                          <span style={{ fontSize: "14px", fontWeight: "600", color: "var(--danger-neon)" }}>
                            ⚠️ {category} ({items.length})
                          </span>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                          {items.map((item, idx) => (
                            <div
                              key={item.id}
                              style={{
                                padding: "10px",
                                backgroundColor: selectedFailureItem?.id === item.id ? "var(--bg-card-hover)" : "var(--bg-dark)",
                                border: selectedFailureItem?.id === item.id ? "1px solid var(--emerald-bright)" : "1px solid #21262d",
                                borderRadius: "6px",
                                cursor: "pointer",
                                fontSize: "12px"
                              }}
                              onClick={() => setSelectedFailureItem(item)}
                            >
                              <div style={{ color: "var(--text-muted)", marginBottom: "4px" }}>Sample ID: {item.id.slice(0, 8)}...</div>
                              <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {item.input_text}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Right Column: Detailed Inspector Card */}
                  <div>
                    {selectedFailureItem ? (
                      <div className="panel" style={{ sticky: "top", top: "100px" }}>
                        <div className="panel-header">
                          <span className="panel-title" style={{ color: "var(--danger-neon)" }}>Failure Diagnostic Inspector</span>
                        </div>
                        
                        <div style={{ marginBottom: "12px" }}>
                          <span className="form-label">Input Prompt Question</span>
                          <p style={{ padding: "10px", backgroundColor: "var(--bg-dark)", border: "1px solid #21262d", borderRadius: "6px", fontSize: "12px" }}>
                            {selectedFailureItem.input_text}
                          </p>
                        </div>

                        <div style={{ marginBottom: "12px" }}>
                          <span className="form-label">Expected Output (Ground Truth)</span>
                          <p style={{ padding: "10px", backgroundColor: "var(--bg-dark)", border: "1px solid #21262d", borderRadius: "6px", fontSize: "12px", color: "var(--emerald-bright)" }}>
                            {selectedFailureItem.expected_output}
                          </p>
                        </div>

                        <div style={{ marginBottom: "12px" }}>
                          <span className="form-label">Model Generated Output</span>
                          <pre style={{ backgroundColor: "var(--bg-dark)", padding: "10px", borderRadius: "6px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid #21262d", fontFamily: "monospace", color: "#f85149" }}>
                            {selectedFailureItem.generated_output}
                          </pre>
                        </div>

                        <div style={{ borderTop: "1px solid #21262d", paddingTop: "12px", display: "flex", flexWrap: "wrap", gap: "10px", fontSize: "11px", color: "var(--text-muted)" }}>
                          <span><strong>Failure Category:</strong> {selectedFailureItem.failure_category}</span>
                          <span><strong>Latency:</strong> {selectedFailureItem.latency.toFixed(2)}s</span>
                          <span><strong>Cost:</strong> ${selectedFailureItem.cost.toFixed(4)}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="panel" style={{ textAlign: "center", padding: "40px" }}>
                        <p style={{ color: "var(--text-muted)" }}>Select a failed item from the left categories list to inspect it.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
