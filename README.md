# Generic ML Experimentation and Evaluation Platform

An enterprise-grade ML experimentation and evaluation platform designed to register datasets, models, and prompts, run parallel evaluations using a database-backed reliable job queue, calculate complex NLP/agent metrics, diagnose failure clusters, and compare results inside an interactive dashboard.

---

## 🏗️ Architecture Overview

```text
                +-----------------------+
                |  Dataset Registry     |
                +-----------+-----------+
                            |
                            v
                +-----------------------+
                |  Experiment Manager   |
                +-----------+-----------+
                            |
          +-----------------+------------------+
          |                                    |
          v                                    v
+--------------------+              +----------------------+
| Inference Engine   |              | Agent Runner         |
+--------------------+              +----------------------+
          |                                    |
          +-----------------+------------------+
                            |
                            v
                +-----------------------+
                | Evaluation Engine     |
                +-----------+-----------+
                            |
                            v
                +-----------------------+
                | Report Generator      |
                +-----------+-----------+
                            |
                            v
                Dashboard / Leaderboards
```

The platform is designed around a decoupled, thread-safe asynchronous architecture:
1. **FastAPI Web Endpoint:** Accepts dataset additions, model setups, and experiment launches.
2. **SQLite WAL Database:** Stores all configuration mappings, logs, and job statuses. Implements optimistic lock transactions to support multi-process/thread workers.
3. **Queue Worker Pool:** Polls jobs, triggers evaluation workflows, updates status steps, and handles backoffs and Dead Letter Queue (DLQ) state transitions.
4. **Plugin Metrics Engine:** Decoupled evaluator classes calculate task-specific scores (BLEU, ROUGE, Faithfulness, Safety refusal, Tool errors, LLM-as-a-Judge).
5. **Vite React UI:** Custom-styled dark glassmorphism (emerald/graphite theme) dashboard showing live updates, Pareto plots, side-by-side run comparisons, and failed log diagnostic inspectors.

---

## ⚡ Key Features

1. **Dataset Registry:** Support custom tasks, license profiles, token lengths, and data splits.
2. **Model Registry & Adapters:** Built-in adapters for OpenAI, Anthropic, Gemini, Ollama (Local), and a **Mock Adapter** which generates task-appropriate synthetic responses for zero-setup, zero-cost pipeline testing.
3. **Prompt Registry:** Draft and version prompt templates with placeholder variables (e.g. `{{question}}`, `{{context}}`).
4. **Reliable Job Queue:** Transactional queue polling with exponential retry backoff, lease visibility heartbeats, and automatic dead-letter recovery.
5. **Evaluation Engine (Plug-in Architecture):** Modular evaluators for Classification, Generation overlap, LLM-as-a-Judge, Agents, RAG alignment, Safety, and Hallucination citation analysis.
6. **Failure Diagnostic Center:** Algorithmic clustering of failing runs into distinct categories (Math Error, Coding Bug, Hallucination, Formatting, and Reasoning Slips).
7. **Model Comparison Workspace:** Interactive side-by-side run inspector comparing summary metrics and prompt logs.
8. **Interactive Leaderboard:** Domain-specific (Math, QA, RAG, Safety) rankings by accuracy, cost, and latency.

---

## 📁 Repository Structure

```text
llm-evaluation-platform/
├── backend/
│   ├── main.py                 # FastAPI application routes & seed generator
│   ├── db.py                   # SQLAlchemy connection & WAL mode pragmas
│   ├── models.py               # Database schemas (Datasets, Models, Jobs, etc.)
│   ├── schemas.py              # Pydantic serialization models
│   ├── queue_engine.py         # DB-backed Job queue worker pool & lease sweeper
│   ├── inference_engine.py     # Adapters (Mock, OpenAI, Anthropic, Gemini, Ollama)
│   ├── evaluation_engine.py    # Metric plugins (BLEU, ROUGE, RAG, Safety, LLM-Judge)
│   ├── failure_analyzer.py     # Log diagnostics and failure clustering
│   ├── reporter.py             # Markdown and styled HTML export generators
│   └── tests/
│       └── test_evaluation_platform.py  # Unit test suite
├── frontend/
│   ├── index.html
│   ├── vite.config.js          # Vite config routing compilation to backend/static
│   ├── src/
│   │   ├── main.jsx
│   │   ├── index.css           # Custom Emerald/Graphite design system stylesheet
│   │   ├── App.jsx             # React layout nav shell
│   │   └── views/
│   │       ├── Dashboard.jsx   # Stats, SVG charts, and queue metrics
│   │       ├── Datasets.jsx    # Dataset list and additions
│   │       ├── Models.jsx      # Model endpoint configs
│   │       ├── Prompts.jsx     # Prompt engineering sandbox
│   │       ├── Experiments.jsx # Launcher form and side-by-side model comparator
│   │       ├── Leaderboards.jsx# Rankings by accuracy, cost, and latency
│   │       └── FailureAnalysis.jsx # Failure diagnostics categorized lists
└── README.md
```

---

## 🚀 Setup & Running Guide

### Prerequisites
- Python 3.10+
- Node.js & npm

### 1. Initialize Python Environment & Install Dependencies
Run the following from the project root directory:
```bash
# Create local virtual environment
python3 -m venv .venv

# Activate and install packages
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pytest pydantic requests jinja2
```

### 2. Compile Frontend Assets
Building compiles the Vite assets and places them inside the FastAPI static folder:
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Launch Backend & UI Server
Run uvicorn. It will automatically initialize the database, seed mock evaluation records, mount the UI, and start the queue worker pool:
```bash
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --port 8000
```
Open **[http://localhost:8000/](http://localhost:8000/)** in your browser to view the platform!

---

## 🧪 Running Automated Tests

Run the test suite checking the database job queue, metric plugins, and adapters:
```bash
PYTHONPATH=. .venv/bin/pytest backend/tests/
```

---

## 🧩 Extension Guide (Plug-in Architecture)

### 1. Adding a Custom Evaluator
To add a new metric, create a class in [backend/evaluation_engine.py](file:///Users/fbin-blr-0025/finbox-work/llm-evaluation-platform/backend/evaluation_engine.py) that inherits from `BaseEvaluator`, implement the `evaluate` method, and register it inside `EvaluationEngine.evaluate_sample`:

```python
class ToxicityEvaluator(BaseEvaluator):
    def evaluate(self, generated_text: str, ground_truth: str = None, context: str = None, metadata: dict = None) -> dict:
        # Custom logic
        score = 0.0
        if "bad_word" in generated_text.lower():
            score = 1.0
        return {"toxicity_score": score}
```

### 2. Adding a Custom Model Adapter
To connect to another LLM api, define a class in [backend/inference_engine.py](file:///Users/fbin-blr-0025/finbox-work/llm-evaluation-platform/backend/inference_engine.py) inheriting from `BaseModelAdapter`, implement `generate`, and update the factory builder in `InferenceEngine.get_adapter`:

```python
class CustomLlamaAdapter(BaseModelAdapter):
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 512, seed: int = None) -> dict:
        # Custom HTTP request logic
        return {
            "text": "Generated response",
            "prompt_tokens": 12,
            "completion_tokens": 18,
            "latency": 0.45,
            "cost": 0.00012,
            "provider_raw": {}
        }
```
