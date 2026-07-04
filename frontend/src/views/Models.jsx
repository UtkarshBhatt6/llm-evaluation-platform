import React, { useState, useEffect } from "react";

export default function Models() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  // Form fields
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("");
  const [provider, setProvider] = useState("Mock");
  const [contextLength, setContextLength] = useState(8192);
  const [inputPrice, setInputPrice] = useState(0.0);
  const [outputPrice, setOutputPrice] = useState(0.0);
  const [latencyAvg, setLatencyAvg] = useState(0.5);

  const fetchModels = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/models");
      const data = await res.json();
      setModels(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load models:", err);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!id || !name || !version) return;

    const payload = {
      id,
      name,
      version,
      provider,
      context_length: parseInt(contextLength),
      pricing_input_1k: parseFloat(inputPrice),
      pricing_output_1k: parseFloat(outputPrice),
      latency_avg: parseFloat(latencyAvg)
    };

    try {
      const res = await fetch("http://localhost:8000/api/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowForm(false);
        fetchModels();
        // Reset form
        setId("");
        setName("");
        setVersion("");
        setProvider("Mock");
        setInputPrice(0.0);
        setOutputPrice(0.0);
      } else {
        const errData = await res.json();
        alert(`Error: ${errData.detail}`);
      }
    } catch (err) {
      console.error("Failed to save model:", err);
    }
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Model Registry</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Manage models, specify context capacities, API latency records, and token-based pricing structures.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "View Models" : "Register Model"}
        </button>
      </div>

      {showForm ? (
        <div className="panel" style={{ maxWidth: "600px", margin: "0 auto" }}>
          <div className="panel-header">
            <span className="panel-title">Add New Model Configuration</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Model ID (unique string, e.g. openai/gpt-4o)</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. deepseek/deepseek-coder" 
                value={id}
                onChange={(e) => setId(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Model Name</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. DeepSeek Coder V2" 
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
                  placeholder="e.g. 2026-06" 
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Provider</label>
                <select className="form-select" value={provider} onChange={(e) => setProvider(e.target.value)}>
                  <option value="OpenAI">OpenAI API</option>
                  <option value="Gemini">Google Gemini API</option>
                  <option value="Anthropic">Anthropic Claude API</option>
                  <option value="Ollama">Ollama (Local Endpoint)</option>
                  <option value="HuggingFace">HuggingFace Inference API</option>
                  <option value="Mock">Mock Testing Provider</option>
                </select>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Context Length (tokens)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  value={contextLength}
                  onChange={(e) => setContextLength(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Avg Latency (seconds)</label>
                <input 
                  type="number" 
                  step="0.01" 
                  className="form-input" 
                  value={latencyAvg}
                  onChange={(e) => setLatencyAvg(e.target.value)}
                />
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Pricing per 1K Input Tokens (USD)</label>
                <input 
                  type="number" 
                  step="0.000001" 
                  className="form-input" 
                  value={inputPrice}
                  onChange={(e) => setInputPrice(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Pricing per 1K Output Tokens (USD)</label>
                <input 
                  type="number" 
                  step="0.000001" 
                  className="form-input" 
                  value={outputPrice}
                  onChange={(e) => setOutputPrice(e.target.value)}
                />
              </div>
            </div>
            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "10px" }}>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Save Model</button>
            </div>
          </form>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Registered Model Adapters</span>
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {models.length} registered</span>
          </div>
          {loading ? (
            <p style={{ color: "var(--text-muted)" }}>Loading models...</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Model Name</th>
                  <th>Provider</th>
                  <th>Context limit</th>
                  <th>Pricing (Input/Output 1K)</th>
                  <th>Avg Latency</th>
                  <th>Version</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.id}>
                    <td className="strong" style={{ fontFamily: "monospace", fontSize: "13px" }}>{model.id}</td>
                    <td>{model.name}</td>
                    <td>
                      <span className="badge badge-completed" style={{ background: "rgba(52, 211, 153, 0.08)", color: "#58a6ff", borderColor: "rgba(88, 166, 255, 0.2)" }}>
                        {model.provider}
                      </span>
                    </td>
                    <td>{model.context_length.toLocaleString()} tokens</td>
                    <td>
                      {model.pricing_input_1k === 0 && model.pricing_output_1k === 0 ? (
                        <span style={{ color: "var(--emerald-bright)" }}>Free (Local)</span>
                      ) : (
                        `$${model.pricing_input_1k.toFixed(4)} / $${model.pricing_output_1k.toFixed(4)}`
                      )}
                    </td>
                    <td>{model.latency_avg} seconds</td>
                    <td style={{ color: "var(--text-muted)" }}>{model.version}</td>
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
