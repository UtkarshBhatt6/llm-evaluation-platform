import React, { useState, useEffect } from "react";

export default function Prompts() {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  // Form fields
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("1.0");
  const [content, setContent] = useState("");
  const [author, setAuthor] = useState("");
  const [task, setTask] = useState("QA");
  const [variables, setVariables] = useState("question");

  const fetchPrompts = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/prompts");
      const data = await res.json();
      setPrompts(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load prompts:", err);
    }
  };

  useEffect(() => {
    fetchPrompts();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!id || !name || !content) return;

    const varsArray = variables.split(",").map(v => v.trim()).filter(Boolean);

    const payload = {
      id,
      name,
      version,
      content,
      author,
      task,
      variables: varsArray
    };

    try {
      const res = await fetch("http://localhost:8000/api/prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowForm(false);
        fetchPrompts();
        // Reset form
        setId("");
        setName("");
        setContent("");
        setVariables("question");
      } else {
        const errData = await res.json();
        alert(`Error: ${errData.detail}`);
      }
    } catch (err) {
      console.error("Failed to save prompt:", err);
    }
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Prompt Template Registry</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Design and version prompt templates with placeholders like <code>{"{{question}}"}</code> and <code>{"{{context}}"}</code>.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "View Prompts" : "Register Prompt"}
        </button>
      </div>

      {showForm ? (
        <div className="panel" style={{ maxWidth: "700px", margin: "0 auto" }}>
          <div className="panel-header">
            <span className="panel-title">Add New Prompt Template</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div className="form-group">
                <label className="form-label">Prompt ID (unique key)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. cot_math_v3" 
                  value={id}
                  onChange={(e) => setId(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Template Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Chain of Thought Math" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
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
                  <option value="Math">Math</option>
                  <option value="QA">QA (General)</option>
                  <option value="RAG">RAG</option>
                  <option value="Agent">Agent</option>
                  <option value="Safety">Safety</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Author Name</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Prompt Engineering Team" 
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Template Variables (comma separated)</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="question, context" 
                value={variables}
                onChange={(e) => setVariables(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Prompt Content Template</label>
              <textarea 
                className="form-textarea" 
                placeholder="Use placeholders like {{question}} and {{context}}..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
              />
            </div>
            <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "10px" }}>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Save Template</button>
            </div>
          </form>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Active Prompts</span>
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>Total {prompts.length} registered</span>
          </div>
          {loading ? (
            <p style={{ color: "var(--text-muted)" }}>Loading prompts...</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "20px" }}>
              {prompts.map((prompt) => (
                <div key={prompt.id} style={{ border: "1px solid var(--border-dim)", borderRadius: "8px", padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                    <div>
                      <strong style={{ color: "var(--emerald-bright)", fontSize: "15px" }}>{prompt.name}</strong>
                      <span style={{ color: "var(--text-muted)", fontSize: "12px", marginLeft: "10px" }}>ID: {prompt.id}</span>
                    </div>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <span className="badge badge-completed" style={{ background: "rgba(52, 211, 153, 0.08)" }}>{prompt.task}</span>
                      <span className="badge badge-pending">v{prompt.version}</span>
                    </div>
                  </div>
                  <pre style={{ 
                    backgroundColor: "var(--bg-dark)", 
                    padding: "12px", 
                    borderRadius: "6px", 
                    color: "var(--text-main)", 
                    fontSize: "13px", 
                    whiteSpace: "pre-wrap",
                    fontFamily: "monospace",
                    border: "1px solid #21262d",
                    marginBottom: "10px"
                  }}>
                    {prompt.content}
                  </pre>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--text-muted)" }}>
                    <span><strong>Author:</strong> {prompt.author || "System"}</span>
                    <span><strong>Placeholders:</strong> {prompt.variables ? prompt.variables.join(", ") : "None"}</span>
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
