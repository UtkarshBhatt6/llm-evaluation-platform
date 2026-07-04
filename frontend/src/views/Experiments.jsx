import React, { useState, useEffect } from "react";

export default function Experiments() {
  const [experiments, setExperiments] = useState([]);
  const [completedRuns, setCompletedRuns] = useState([]);
  const [models, setModels] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [prompts, setPrompts] = useState([]);
  
  const [showLauncher, setShowLauncher] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form Launcher fields
  const [name, setName] = useState("");
  const [modelId, setModelId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [promptId, setPromptId] = useState("");
  const [temp, setTemp] = useState(0.7);
  const [topP, setTopP] = useState(0.95);
  const [maxTokens, setMaxTokens] = useState(256);
  const [seed, setSeed] = useState(42);

  // Compare Mode fields
  const [compareMode, setCompareMode] = useState(false);
  const [runAId, setRunAId] = useState("");
  const [runBId, setRunBId] = useState("");
  const [runADetail, setRunADetail] = useState(null);
  const [runBDetail, setRunBDetail] = useState(null);
  const [selectedLogIndex, setSelectedLogIndex] = useState(0);

  const fetchRegistryData = async () => {
    try {
      const [resExp, resModels, resDatasets, resPrompts, resRuns] = await Promise.all([
        fetch("http://localhost:8000/api/experiments"),
        fetch("http://localhost:8000/api/models"),
        fetch("http://localhost:8000/api/datasets"),
        fetch("http://localhost:8000/api/prompts"),
        fetch("http://localhost:8000/api/results")
      ]);
      
      const [dataExp, dataModels, dataDatasets, dataPrompts, dataRuns] = await Promise.all([
        resExp.json(), resModels.json(), resDatasets.json(), resPrompts.json(), resRuns.json()
      ]);
      
      setExperiments(dataExp);
      setModels(dataModels);
      setDatasets(dataDatasets);
      setPrompts(dataPrompts);
      setCompletedRuns(dataRuns.filter(r => r.status === "completed"));
      
      // Select first options as defaults in launcher form
      if (dataModels.length) setModelId(dataModels[0].id);
      if (dataDatasets.length) setDatasetId(dataDatasets[0].id);
      if (dataPrompts.length) setPromptId(dataPrompts[0].id);
      
      setLoading(false);
    } catch (err) {
      console.error("Failed to load launcher assets:", err);
    }
  };

  useEffect(() => {
    fetchRegistryData();
  }, []);

  const handleLaunch = async (e) => {
    e.preventDefault();
    if (!name || !modelId || !datasetId || !promptId) return;

    const payload = {
      name,
      model_id: modelId,
      dataset_id: datasetId,
      prompt_id: promptId,
      temperature: parseFloat(temp),
      top_p: parseFloat(topP),
      max_tokens: parseInt(maxTokens),
      seed: parseInt(seed)
    };

    try {
      // 1. Create experiment
      const resExp = await fetch("http://localhost:8000/api/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const dataExp = await resExp.json();
      
      if (resExp.ok) {
        // 2. Trigger evaluate (pushes run task to reliable job queue)
        await fetch(`http://localhost:8000/api/evaluate?experiment_id=${dataExp.id}`, { method: "POST" });
        setShowLauncher(false);
        fetchRegistryData();
        setName("");
      } else {
        alert(`Launch Error: ${dataExp.detail}`);
      }
    } catch (err) {
      console.error("Failed to launch evaluation run:", err);
    }
  };

  // Compare Runs trigger
  const handleCompare = async () => {
    if (!runAId || !runBId) return;
    try {
      const [resA, resB] = await Promise.all([
        fetch(`http://localhost:8000/api/results/${runAId}`),
        fetch(`http://localhost:8000/api/results/${runBId}`)
      ]);
      const dataA = await resA.json();
      const dataB = await resB.json();
      setRunADetail(dataA);
      setRunBDetail(dataB);
      setSelectedLogIndex(0);
    } catch (err) {
      console.error("Failed to fetch compare data:", err);
    }
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Experimentation Hub</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Design, deploy, and benchmark prompt strategies across different model nodes.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn-secondary" onClick={() => { setCompareMode(!compareMode); setRunADetail(null); setRunBDetail(null); }}>
            {compareMode ? "Launch/List Mode" : "Model Comparison Workspace"}
          </button>
          {!compareMode && (
            <button className="btn-primary" onClick={() => setShowLauncher(!showLauncher)}>
              {showLauncher ? "View Experiments" : "Deploy Experiment"}
            </button>
          )}
        </div>
      </div>

      {compareMode ? (
        /* ------------------ COMPARISON WORKSPACE ------------------ */
        <div>
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Select Runs to Compare</span>
            </div>
            <div style={{ display: "flex", gap: "20px", alignItems: "flex-end" }}>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label">Run A (Base Model)</label>
                <select className="form-select" value={runAId} onChange={(e) => setRunAId(e.target.value)}>
                  <option value="">-- Choose Completed Run --</option>
                  {completedRuns.map(r => (
                    <option key={r.id} value={r.id}>{r.experiment_id.replace("exp_run_", "")} (Run: {r.id.slice(0, 8)})</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label">Run B (Comparison Model)</label>
                <select className="form-select" value={runBId} onChange={(e) => setRunBId(e.target.value)}>
                  <option value="">-- Choose Completed Run --</option>
                  {completedRuns.map(r => (
                    <option key={r.id} value={r.id}>{r.experiment_id.replace("exp_run_", "")} (Run: {r.id.slice(0, 8)})</option>
                  ))}
                </select>
              </div>
              <button className="btn-primary" onClick={handleCompare} disabled={!runAId || !runBId}>Compare Runs</button>
            </div>
          </div>

          {runADetail && runBDetail && (
            <div>
              {/* Aggregated Stats Comparison */}
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Comparative Metrics Overview</span>
                </div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th style={{ color: "var(--emerald-bright)" }}>Run A: {runADetail.model.name}</th>
                      <th style={{ color: "#58a6ff" }}>Run B: {runBDetail.model.name}</th>
                      <th>Difference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Latency */}
                    <tr>
                      <td className="strong">Average Latency</td>
                      <td>{runADetail.metrics_summary.avg_latency.toFixed(3)}s</td>
                      <td>{runBDetail.metrics_summary.avg_latency.toFixed(3)}s</td>
                      <td style={{ color: runADetail.metrics_summary.avg_latency > runBDetail.metrics_summary.avg_latency ? "var(--emerald-bright)" : "var(--danger-neon)" }}>
                        {(runBDetail.metrics_summary.avg_latency - runADetail.metrics_summary.avg_latency).toFixed(3)}s
                      </td>
                    </tr>
                    {/* Cost */}
                    <tr>
                      <td className="strong">Total Run Cost</td>
                      <td>${runADetail.metrics_summary.total_cost.toFixed(4)}</td>
                      <td>${runBDetail.metrics_summary.total_cost.toFixed(4)}</td>
                      <td style={{ color: runADetail.metrics_summary.total_cost > runBDetail.metrics_summary.total_cost ? "var(--emerald-bright)" : "var(--danger-neon)" }}>
                        ${(runBDetail.metrics_summary.total_cost - runADetail.metrics_summary.total_cost).toFixed(4)}
                      </td>
                    </tr>
                    {/* Accuracy or Task Success */}
                    {("accuracy" in runADetail.metrics_summary) && (
                      <tr>
                        <td className="strong">Average Accuracy</td>
                        <td>{(runADetail.metrics_summary.accuracy * 100).toFixed(0)}%</td>
                        <td>{(runBDetail.metrics_summary.accuracy * 100).toFixed(0)}%</td>
                        <td style={{ color: runBDetail.metrics_summary.accuracy >= runADetail.metrics_summary.accuracy ? "var(--emerald-bright)" : "var(--danger-neon)" }}>
                          {((runBDetail.metrics_summary.accuracy - runADetail.metrics_summary.accuracy) * 100).toFixed(0)}%
                        </td>
                      </tr>
                    )}
                    {/* RAG Faithfulness */}
                    {("faithfulness" in runADetail.metrics_summary) && (
                      <tr>
                        <td className="strong">Context Faithfulness</td>
                        <td>{(runADetail.metrics_summary.faithfulness * 100).toFixed(0)}%</td>
                        <td>{(runBDetail.metrics_summary.faithfulness * 100).toFixed(0)}%</td>
                        <td>{((runBDetail.metrics_summary.faithfulness - runADetail.metrics_summary.faithfulness) * 100).toFixed(0)}%</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Sample-by-Sample Diff Inspector */}
              <div className="split-layout">
                {/* Sidebar index */}
                <div className="split-sidebar">
                  <span className="form-label">Evaluation Prompts ({runADetail.logs.length})</span>
                  {runADetail.logs.map((log, idx) => (
                    <div 
                      key={log.id} 
                      className={`sidebar-item ${selectedLogIndex === idx ? "active" : ""}`}
                      onClick={() => setSelectedLogIndex(idx)}
                    >
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>Sample #{idx + 1}</div>
                      <div style={{ fontSize: "12px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {log.input_text}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Display comparisons */}
                <div className="panel" style={{ marginBottom: 0 }}>
                  <div className="panel-header">
                    <span className="panel-title">Response Comparison</span>
                  </div>
                  
                  <div style={{ marginBottom: "16px" }}>
                    <span className="form-label">Prompt Question</span>
                    <p style={{ padding: "10px", backgroundColor: "var(--bg-dark)", border: "1px solid #21262d", borderRadius: "6px", fontSize: "13px" }}>
                      {runADetail.logs[selectedLogIndex].input_text}
                    </p>
                  </div>

                  <div style={{ marginBottom: "16px" }}>
                    <span className="form-label">Expected Output (Ground Truth)</span>
                    <p style={{ padding: "10px", backgroundColor: "var(--bg-dark)", border: "1px solid #21262d", borderRadius: "6px", fontSize: "13px", color: "var(--emerald-bright)" }}>
                      {runADetail.logs[selectedLogIndex].expected_output || "No ground truth provided"}
                    </p>
                  </div>

                  <div className="compare-container">
                    {/* Run A completion */}
                    <div style={{ border: "1px solid var(--border-dim)", borderRadius: "8px", padding: "14px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                        <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--emerald-bright)" }}>Run A: {runADetail.model.name}</span>
                        <span className={`badge badge-${runADetail.logs[selectedLogIndex].is_failure ? "failed" : "completed"}`}>
                          {runADetail.logs[selectedLogIndex].is_failure ? "Incorrect" : "Correct"}
                        </span>
                      </div>
                      <pre style={{ backgroundColor: "var(--bg-dark)", padding: "10px", borderRadius: "6px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid #21262d", minHeight: "100px", fontFamily: "monospace" }}>
                        {runADetail.logs[selectedLogIndex].generated_output}
                      </pre>
                      <div style={{ display: "flex", gap: "10px", marginTop: "10px", fontSize: "11px", color: "var(--text-muted)" }}>
                        <span>Latency: {runADetail.logs[selectedLogIndex].latency.toFixed(2)}s</span>
                        <span>Cost: ${runADetail.logs[selectedLogIndex].cost.toFixed(4)}</span>
                      </div>
                    </div>

                    {/* Run B completion */}
                    <div style={{ border: "1px solid var(--border-dim)", borderRadius: "8px", padding: "14px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                        <span style={{ fontSize: "13px", fontWeight: "600", color: "#58a6ff" }}>Run B: {runBDetail.model.name}</span>
                        <span className={`badge badge-${runBDetail.logs[selectedLogIndex].is_failure ? "failed" : "completed"}`}>
                          {runBDetail.logs[selectedLogIndex].is_failure ? "Incorrect" : "Correct"}
                        </span>
                      </div>
                      <pre style={{ backgroundColor: "var(--bg-dark)", padding: "10px", borderRadius: "6px", fontSize: "12px", whiteSpace: "pre-wrap", border: "1px solid #21262d", minHeight: "100px", fontFamily: "monospace" }}>
                        {runBDetail.logs[selectedLogIndex].generated_output}
                      </pre>
                      <div style={{ display: "flex", gap: "10px", marginTop: "10px", fontSize: "11px", color: "var(--text-muted)" }}>
                        <span>Latency: {runBDetail.logs[selectedLogIndex].latency.toFixed(2)}s</span>
                        <span>Cost: ${runBDetail.logs[selectedLogIndex].cost.toFixed(4)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : showLauncher ? (
        /* ------------------ LAUNCHER FORM ------------------ */
        <div className="panel" style={{ maxWidth: "700px", margin: "0 auto" }}>
          <div className="panel-header">
            <span className="panel-title">Deploy Evaluation Experiment</span>
          </div>
          <form onSubmit={handleLaunch}>
            <div className="form-group">
              <label className="form-label">Experiment Name</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Llama3 GSM8K prompt-v2 tuning" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            
            <div className="form-group">
              <label className="form-label">Select Model Node</label>
              <select className="form-select" value={modelId} onChange={(e) => setModelId(e.target.value)}>
                {models.map(m => (
                  <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
                ))}
              </select>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Select Evaluation Dataset</label>
                <select className="form-select" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                  {datasets.map(d => (
                    <option key={d.id} value={d.id}>{d.name} ({d.task})</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Select Prompt Strategy</label>
                <select className="form-select" value={promptId} onChange={(e) => setPromptId(e.target.value)}>
                  {prompts.map(p => (
                    <option key={p.id} value={p.id}>{p.name} (v{p.version})</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Temperature</label>
                <input 
                  type="number" 
                  step="0.05" 
                  className="form-input" 
                  value={temp}
                  onChange={(e) => setTemp(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Top P</label>
                <input 
                  type="number" 
                  step="0.05" 
                  className="form-input" 
                  value={topP}
                  onChange={(e) => setTopP(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Max Tokens</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Seed</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "10px" }}>
              <button type="button" className="btn-secondary" onClick={() => setShowLauncher(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Launch Queue Job</button>
            </div>
          </form>
        </div>
      ) : (
        /* ------------------ EXPERIMENTS LIST ------------------ */
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Configured Experiments</span>
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {experiments.length} runs</span>
          </div>
          {loading ? (
            <p style={{ color: "var(--text-muted)" }}>Loading experiments...</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Experiment Name</th>
                  <th>Model</th>
                  <th>Dataset</th>
                  <th>Prompt</th>
                  <th>Parameters</th>
                  <th>Last Status</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.id}>
                    <td className="strong" style={{ fontFamily: "monospace", fontSize: "13px" }}>{exp.id.slice(0, 8)}...</td>
                    <td>{exp.name}</td>
                    <td>{exp.model_id.replace("openai/", "").replace("meta/", "").replace("gemini/", "")}</td>
                    <td>{exp.dataset_id}</td>
                    <td>{exp.prompt_id}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                      T={exp.temperature} / Seed={exp.seed}
                    </td>
                    <td>
                      <span className={`badge badge-${exp.status}`}>
                        {exp.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
