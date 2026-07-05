import React, { useState, useEffect } from "react";

export default function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  // Form fields
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("1.0");
  const [task, setTask] = useState("QA");
  const [license, setLicense] = useState("MIT");
  const [numSamples, setNumSamples] = useState(5);
  const [avgTokens, setAvgTokens] = useState(120);
  const [csvText, setCsvText] = useState("");

  const fetchDatasets = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/datasets");
      const data = await res.json();
      setDatasets(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load datasets:", err);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const parseCSV = (text) => {
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (lines.length < 2) return [];

    const parseLine = (line) => {
      const result = [];
      let current = "";
      let inQuotes = false;
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"' || char === "'") {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim().replace(/^["']|["']$/g, ''));
          current = "";
        } else {
          current += char;
        }
      }
      result.push(current.trim().replace(/^["']|["']$/g, ''));
      return result;
    };

    const headers = parseLine(lines[0]);
    const parsed = [];

    for (let i = 1; i < lines.length; i++) {
      const cols = parseLine(lines[i]);
      if (cols.length === headers.length) {
        const row = {};
        headers.forEach((h, idx) => {
          row[h] = cols[idx];
        });
        parsed.push(row);
      }
    }
    return parsed;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!id || !name) return;

    let customSamples = null;
    let finalNumSamples = parseInt(numSamples);

    if (csvText.trim()) {
      const parsed = parseCSV(csvText);
      if (parsed.length === 0) {
        alert("Failed to parse CSV samples. Ensure you provide headers (question, ground_truth, context) on the first line.");
        return;
      }
      customSamples = parsed;
      finalNumSamples = parsed.length;
    }
    
    const payload = {
      id,
      name,
      version,
      task,
      license,
      num_samples: finalNumSamples,
      avg_tokens: parseInt(avgTokens),
      splits: ["test"],
      samples: customSamples,
      metadata_info: { registered_by: "UI Client" }
    };

    try {
      const res = await fetch("http://localhost:8000/api/datasets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowForm(false);
        fetchDatasets();
        // Reset form
        setId("");
        setName("");
        setCsvText("");
      } else {
        const errData = await res.json();
        alert(`Error: ${errData.detail}`);
      }
    } catch (err) {
      console.error("Failed to save dataset:", err);
    }
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Dataset Registry</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            View and register evaluations datasets (JSONL, CSV, or Hugging Face imports).
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "View Datasets" : "Register Dataset"}
        </button>
      </div>

      {showForm ? (
        <div className="panel" style={{ maxWidth: "600px", margin: "0 auto" }}>
          <div className="panel-header">
            <span className="panel-title">Add New Dataset</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Dataset ID (unique string)</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. gsm8k_math_v2" 
                value={id}
                onChange={(e) => setId(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Display Name</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. GSM8K Math benchmark" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Version</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Task Category</label>
                <select className="form-select" value={task} onChange={(e) => setTask(e.target.value)}>
                  <option value="Math">Math Reasoning</option>
                  <option value="QA">Question Answering (General)</option>
                  <option value="RAG">RAG Retrieval Alignment</option>
                  <option value="Agent">Agent tool flow</option>
                  <option value="Safety">Safety & Jailbreak</option>
                </select>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Number of Samples</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={numSamples}
                  onChange={(e) => setNumSamples(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Average Tokens per Sample</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={avgTokens}
                  onChange={(e) => setAvgTokens(e.target.value)}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">License</label>
              <input 
                type="text" 
                className="form-input" 
                value={license}
                onChange={(e) => setLicense(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ marginBottom: "16px" }}>
              <label className="form-label">Upload or Paste CSV samples (Optional)</label>
              <textarea 
                className="form-input" 
                rows="4" 
                placeholder="question,ground_truth,context&#10;&quot;What is 2+2?&quot;,&quot;4&quot;,&quot;&quot;&#10;&quot;What color is Mars?&quot;,&quot;red&quot;,&quot;&quot;"
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                style={{ fontFamily: "monospace", fontSize: "11px", backgroundColor: "var(--bg-dark)", color: "var(--text)", border: "1px solid #21262d", borderRadius: "6px", width: "100%", boxSizing: "border-box" }}
              />
              <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                Add raw test queries. Column headers MUST be: <strong>question</strong>, <strong>ground_truth</strong>, and optionally <strong>context</strong>.
              </span>
            </div>
            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "10px" }}>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Save Registry</button>
            </div>
          </form>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Registered Datasets</span>
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {datasets.length} registered</span>
          </div>
          {loading ? (
            <p style={{ color: "var(--text-muted)" }}>Loading datasets...</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Dataset Name</th>
                  <th>Task</th>
                  <th>Samples</th>
                  <th>Avg Tokens</th>
                  <th>Version</th>
                  <th>License</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td className="strong" style={{ fontFamily: "monospace", fontSize: "13px" }}>{dataset.id}</td>
                    <td>{dataset.name}</td>
                    <td>
                      <span className="badge badge-completed" style={{ background: "rgba(52, 211, 153, 0.08)" }}>
                        {dataset.task}
                      </span>
                    </td>
                    <td>{dataset.num_samples}</td>
                    <td>{dataset.avg_tokens}</td>
                    <td>v{dataset.version}</td>
                    <td style={{ color: "var(--text-muted)" }}>{dataset.license || "N/A"}</td>
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
