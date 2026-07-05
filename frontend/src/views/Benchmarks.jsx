import React, { useState, useEffect } from "react";

const STANDARD_BENCHMARKS = [
  {
    id: "mmlu_qa",
    name: "MMLU",
    fullName: "Massive Multitask Language Understanding",
    task: "Academic QA",
    samples: 25,
    evaluator: "Exact Match QA",
    description: "Evaluates multi-subject knowledge across humanities, social sciences, history, and STEM.",
    promptId: "zero_shot",
    icon: "📖"
  },
  {
    id: "gsm8k_v1.2",
    name: "GSM8K",
    fullName: "Grade School Math 8k",
    task: "Math Solver",
    samples: 10,
    evaluator: "Math Extraction",
    description: "Measures multi-step mathematical reasoning and basic arithmetical calculations.",
    promptId: "cot_v2",
    icon: "🔢"
  },
  {
    id: "human_eval",
    name: "HumanEval",
    fullName: "OpenAI HumanEval Coding",
    task: "Coding Synthesis",
    samples: 15,
    evaluator: "Code Execution",
    description: "Evaluates Python code writing correctness by testing generated functions against unit checks.",
    promptId: "zero_shot",
    icon: "💻"
  },
  {
    id: "truthful_qa",
    name: "TruthfulQA",
    fullName: "Truthfulness & Hallucination QA",
    task: "Safety & Alignment",
    samples: 12,
    evaluator: "Refusal Guardrails",
    description: "Measures whether models mimic human cognitive biases, rumors, or produce hallucinations.",
    promptId: "zero_shot",
    icon: "🛡️"
  },
  {
    id: "hellaswag",
    name: "HellaSwag",
    fullName: "HellaSwag Commonsense QA",
    task: "Commonsense Reasoning",
    samples: 20,
    evaluator: "Choice Classification",
    description: "Evaluates model understanding of physical situations and logical next-sentence predictions.",
    promptId: "zero_shot",
    icon: "💡"
  },
  {
    id: "arc_challenge",
    name: "ARC Challenge",
    fullName: "AI2 Reasoning Challenge",
    task: "Science QA",
    samples: 15,
    evaluator: "Exact Match QA",
    description: "Science exam questions requiring deep knowledge reasoning, science logic, and inference.",
    promptId: "zero_shot",
    icon: "🔬"
  },
  {
    id: "bbh_reasoning",
    name: "BBH Reasoning",
    fullName: "Big Bench Hard Reasoning",
    task: "Hard Logic",
    samples: 10,
    evaluator: "Exact Match QA",
    description: "Hard reasoning tasks where multi-step logical structures and reasoning chains are critical.",
    promptId: "zero_shot",
    icon: "🧠"
  }
];

export default function Benchmarks() {
  const [models, setModels] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedModels, setSelectedModels] = useState({});
  const [loading, setLoading] = useState(true);
  const [actionStatus, setActionStatus] = useState({});

  const fetchData = async () => {
    try {
      const [resModels, resRuns] = await Promise.all([
        fetch("http://localhost:8000/api/models"),
        fetch("http://localhost:8000/api/results")
      ]);
      const dataModels = await resModels.json();
      const dataRuns = await resRuns.json();

      setModels(dataModels);
      setRuns(dataRuns);

      // Set default selected model for each benchmark card
      if (dataModels.length) {
        const initialSelections = {};
        STANDARD_BENCHMARKS.forEach(b => {
          initialSelections[b.id] = dataModels[0].id;
        });
        setSelectedModels(prev => ({ ...initialSelections, ...prev }));
      }
      setLoading(false);
    } catch (err) {
      console.error("Failed to load benchmark suite models/runs:", err);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll results to update progress bars automatically
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleLaunchBenchmark = async (benchmark) => {
    const targetModelId = selectedModels[benchmark.id];
    if (!targetModelId) return;

    setActionStatus(prev => ({ ...prev, [benchmark.id]: "Launching..." }));

    const payload = {
      name: `Benchmark: ${benchmark.name} (${targetModelId.split("/")[1] || targetModelId})`,
      model_id: targetModelId,
      dataset_id: benchmark.id,
      prompt_id: benchmark.promptId,
      temperature: 0.1, // low temperature for benchmarks
      top_p: 0.9,
      max_tokens: 512,
      seed: 42
    };

    try {
      // 1. Register Experiment
      const resExp = await fetch("http://localhost:8000/api/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const dataExp = await resExp.json();

      if (resExp.ok) {
        // 2. Queue Run
        await fetch(`http://localhost:8000/api/evaluate?experiment_id=${dataExp.id}`, { method: "POST" });
        setActionStatus(prev => ({ ...prev, [benchmark.id]: "Queued!" }));
        setTimeout(() => {
          setActionStatus(prev => ({ ...prev, [benchmark.id]: null }));
        }, 3000);
        fetchData();
      } else {
        alert(`Failed to launch benchmark: ${dataExp.detail}`);
        setActionStatus(prev => ({ ...prev, [benchmark.id]: null }));
      }
    } catch (err) {
      console.error("Benchmark launch error:", err);
      setActionStatus(prev => ({ ...prev, [benchmark.id]: null }));
    }
  };

  return (
    <div>
      <div className="view-title-section">
        <div>
          <h1 className="view-title">Standardized Benchmark Suite</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "4px" }}>
            Compare model nodes directly using industry-standard task protocols and datasets.
          </p>
        </div>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}>Loading benchmark parameters...</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "20px" }}>
          {STANDARD_BENCHMARKS.map(b => {
            // Find active running job for this benchmark
            const activeRun = runs.find(r => r.dataset_name.includes(b.name) && (r.status === "pending" || r.status === "running"));
            const lastCompletedRun = runs.find(r => r.dataset_name.includes(b.name) && r.status === "completed");

            return (
              <div className="panel" key={b.id} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                    <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                      <span style={{ fontSize: "28px" }}>{b.icon}</span>
                      <div>
                        <h3 style={{ margin: 0, color: "var(--emerald-bright)", fontSize: "18px" }}>{b.name}</h3>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{b.fullName}</span>
                      </div>
                    </div>
                    <span className="badge" style={{ backgroundColor: "#1f2937", border: "1px solid #374151", color: "var(--text-muted)" }}>
                      {b.task}
                    </span>
                  </div>

                  <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: "1.4", minHeight: "55px", marginBottom: "15px" }}>
                    {b.description}
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", background: "var(--bg-dark)", padding: "10px", borderRadius: "6px", border: "1px solid #21262d", marginBottom: "15px" }}>
                    <div><span style={{ color: "var(--text-muted)" }}>Samples:</span> <strong>{b.samples} items</strong></div>
                    <div><span style={{ color: "var(--text-muted)" }}>Metric:</span> <strong>{b.evaluator}</strong></div>
                  </div>
                </div>

                <div>
                  {activeRun ? (
                    /* Active Running Progress Indicator */
                    <div style={{ margin: "10px 0" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                        <span style={{ color: "var(--emerald-bright)" }}>🤖 Evaluating...</span>
                        <span>{activeRun.progress}%</span>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill" style={{ width: `${activeRun.progress}%` }}></div>
                      </div>
                    </div>
                  ) : (
                    /* Model Selection & Evaluate launch */
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "10px" }}>
                      <div style={{ flex: 1 }}>
                        <select
                          className="form-select"
                          value={selectedModels[b.id] || ""}
                          onChange={(e) => setSelectedModels(prev => ({ ...prev, [b.id]: e.target.value }))}
                          style={{ marginBottom: 0, padding: "8px" }}
                        >
                          {models.map(m => (
                            <option key={m.id} value={m.id}>
                              {m.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <button
                        className="btn-primary"
                        onClick={() => handleLaunchBenchmark(b)}
                        style={{ padding: "8px 16px", whiteSpace: "nowrap" }}
                        disabled={actionStatus[b.id] !== undefined}
                      >
                        {actionStatus[b.id] || "Run"}
                      </button>
                    </div>
                  )}

                  {lastCompletedRun && !activeRun && (
                    <div style={{ marginTop: "12px", fontSize: "11px", color: "var(--text-muted)", display: "flex", justifyContent: "space-between" }}>
                      <span>Last run: {new Date(lastCompletedRun.completed_at || lastCompletedRun.started_at).toLocaleDateString()}</span>
                      <span style={{ color: "var(--emerald-bright)", fontWeight: "bold" }}>Completed ✓</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
