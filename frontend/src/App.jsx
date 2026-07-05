import React, { useState, useEffect } from "react";
import Dashboard from "./views/Dashboard";
import Datasets from "./views/Datasets";
import Benchmarks from "./views/Benchmarks";
import Models from "./views/Models";
import Prompts from "./views/Prompts";
import Experiments from "./views/Experiments";
import Leaderboards from "./views/Leaderboards";
import FailureAnalysis from "./views/FailureAnalysis";

export default function App() {
  const [view, setView] = useState("dashboard");
  const [selectedRunId, setSelectedRunId] = useState("");
  const [jobStats, setJobStats] = useState({ pending: 0, processing: 0, completed: 0, failed: 0, dead_letter: 0 });

  const fetchQueueStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/jobs/stats");
      const data = await res.json();
      setJobStats(data);
    } catch (err) {
      console.error("Failed to fetch header queue stats:", err);
    }
  };

  useEffect(() => {
    fetchQueueStats();
    // Poll header queue status every 4 seconds
    const interval = setInterval(fetchQueueStats, 4000);
    return () => clearInterval(interval);
  }, []);

  const renderActiveView = () => {
    switch (view) {
      case "dashboard":
        return <Dashboard setView={setView} setSelectedRunId={setSelectedRunId} />;
      case "benchmarks":
        return <Benchmarks />;
      case "datasets":
        return <Datasets />;
      case "models":
        return <Models />;
      case "prompts":
        return <Prompts />;
      case "experiments":
        return <Experiments />;
      case "leaderboards":
        return <Leaderboards />;
      case "failure_analysis":
        return <FailureAnalysis runId={selectedRunId} setRunId={setSelectedRunId} />;
      default:
        return <Dashboard setView={setView} setSelectedRunId={setSelectedRunId} />;
    }
  };

  return (
    <div className="app-container">
      {/* Platform Header */}
      <header className="app-header">
        <div className="logo-section">
          <svg className="logo-icon" viewBox="0 0 24 24">
            <path d="M12 2L2 22h20L12 2zm0 4l6.5 13h-13L12 6zm-1 9h2v2h-2v-2zm0-5h2v3h-2v-3z"/>
          </svg>
          <span className="logo-text">Aether ML Eval</span>
        </div>

        {/* Header Tabs */}
        <nav className="nav-links">
          <button className={`nav-tab ${view === "dashboard" ? "active" : ""}`} onClick={() => setView("dashboard")}>Dashboard</button>
          <button className={`nav-tab ${view === "benchmarks" ? "active" : ""}`} onClick={() => setView("benchmarks")}>Benchmark Suite</button>
          <button className={`nav-tab ${view === "datasets" ? "active" : ""}`} onClick={() => setView("datasets")}>Datasets</button>
          <button className={`nav-tab ${view === "models" ? "active" : ""}`} onClick={() => setView("models")}>Models</button>
          <button className={`nav-tab ${view === "prompts" ? "active" : ""}`} onClick={() => setView("prompts")}>Prompts</button>
          <button className={`nav-tab ${view === "experiments" ? "active" : ""}`} onClick={() => setView("experiments")}>Experiments</button>
          <button className={`nav-tab ${view === "leaderboards" ? "active" : ""}`} onClick={() => setView("leaderboards")}>Leaderboard</button>
          <button className={`nav-tab ${view === "failure_analysis" ? "active" : ""}`} onClick={() => setView("failure_analysis")}>Failure Diagnostics</button>
        </nav>

        {/* Live Queue Status Lamp */}
        <div className="header-stats">
          <div className="queue-pill">
            <span className={`status-lamp ${jobStats.processing > 0 ? "active" : "pending"}`}></span>
            <span>Workers: {jobStats.processing} active</span>
          </div>
        </div>
      </header>

      {/* Primary Layout View */}
      <main className="main-content">
        {renderActiveView()}
      </main>
    </div>
  );
}
