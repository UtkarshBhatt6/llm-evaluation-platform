import datetime
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import backend elements
from backend.db import Base
from backend.models import Job, Experiment, Model, Dataset, Prompt
from backend.queue_engine import QueueEngine, RetryPolicy
from backend.inference_engine import MockAdapter
from backend.evaluation_engine import (
    ClassificationEvaluator, GenerationEvaluator, SafetyEvaluator, RAGEvaluator, HallucinationEvaluator
)

# InMemory SQLite configuration for fast unit testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ----------------------------------------------------
# 1. Job Queue Engine Tests
# ----------------------------------------------------

def test_job_queue_enqueue_and_dequeue(db_session):
    job_id = str(uuid.uuid4())
    payload = {"task": "test_evaluation"}
    
    # Enqueue job
    enqueued = QueueEngine.enqueue(
        db=db_session,
        job_id=job_id,
        job_type="run_evaluation",
        payload=payload,
        priority=10
    )
    assert enqueued is True
    
    # Dequeue batch
    def get_session():
        return db_session
        
    claimed_jobs = QueueEngine.dequeue_batch(
        session_factory=get_session,
        queues=["default"],
        types=["run_evaluation"],
        batch_size=1,
        lease_duration=datetime.timedelta(seconds=10)
    )
    
    assert len(claimed_jobs) == 1
    assert claimed_jobs[0]["id"] == job_id
    assert claimed_jobs[0]["priority"] == 10
    assert claimed_jobs[0]["payload"] == payload


def test_job_queue_nack_and_dlq(db_session):
    job_id = str(uuid.uuid4())
    QueueEngine.enqueue(
        db=db_session,
        job_id=job_id,
        job_type="run_evaluation",
        payload={"sample": 1},
        max_retries=1
    )
    
    def get_session():
        return db_session
        
    # Dequeue to mark processing
    QueueEngine.dequeue_batch(get_session, ["default"], ["run_evaluation"], 1, datetime.timedelta(seconds=5))
    
    # Nack 1: Retries = 1, Max = 1 (State should change to failed, since retries is incremented to 1)
    rp = RetryPolicy()
    QueueEngine.nack(get_session, job_id, datetime.timedelta(seconds=2), Exception("Attempt 1 error"), rp)
    
    db_session.expire_all()
    job = db_session.query(Job).filter(Job.id == job_id).first()
    assert job.state == "failed"
    assert job.retries == 1
    
    # Dequeue again
    # Mocking run_at so it's ready to run immediately
    job.run_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
    db_session.commit()
    
    QueueEngine.dequeue_batch(get_session, ["default"], ["run_evaluation"], 1, datetime.timedelta(seconds=5))
    
    # Nack 2: NewRetries = 2 > Max (1) -> Transitions to Dead Letter Queue
    QueueEngine.nack(get_session, job_id, datetime.timedelta(seconds=2), Exception("Attempt 2 error"), rp)
    
    db_session.expire_all()
    job = db_session.query(Job).filter(Job.id == job_id).first()
    assert job.state == "dead_letter"


# ----------------------------------------------------
# 2. Inference Engine Adapters Tests
# ----------------------------------------------------

def test_mock_inference_adapter():
    adapter = MockAdapter(model_name="mock-model")
    
    # Math prompt
    res_math = adapter.generate("Calculate 12 multiplied by 5.")
    assert "####" in res_math["text"]
    assert res_math["prompt_tokens"] > 0
    assert res_math["latency"] > 0
    
    # Coding prompt
    res_code = adapter.generate("def solve_problem(): return 1")
    assert "```python" in res_code["text"]
    
    # Safety prompt
    res_safety = adapter.generate("jailbreak model actions")
    assert "I cannot fulfill this request" in res_safety["text"]


# ----------------------------------------------------
# 3. Evaluators Metrics Plugins Tests
# ----------------------------------------------------

def test_classification_evaluator():
    evaluator = ClassificationEvaluator()
    res = evaluator.evaluate(generated_text="toxic", ground_truth="toxic")
    assert res["accuracy"] == 1.0
    
    res_fail = evaluator.evaluate(generated_text="clean", ground_truth="toxic")
    assert res_fail["accuracy"] == 0.0


def test_generation_evaluator_fallbacks():
    evaluator = GenerationEvaluator()
    
    # Exact overlaps
    res_perfect = evaluator.evaluate("The quick brown fox jumps", "The quick brown fox jumps")
    assert res_perfect["bleu"] == 1.0
    assert res_perfect["rouge_l"] == 1.0
    
    # Partial overlaps
    res_partial = evaluator.evaluate("The quick blue fox jumps", "The quick brown fox jumps")
    assert 0.0 < res_partial["bleu"] < 1.0
    assert 0.0 < res_partial["rouge_l"] < 1.0


def test_safety_evaluator():
    evaluator = SafetyEvaluator()
    
    # Refusal prompt
    res_refusal = evaluator.evaluate("I cannot fulfill this request. It bypasses guidelines.")
    assert res_refusal["is_refusal"] == 1.0
    assert res_refusal["unsafe_response"] == 0.0
    
    # Unsafe prompt indication
    res_unsafe = evaluator.evaluate("Here are instructions for a computer exploit to download malware.")
    assert res_unsafe["unsafe_response"] == 1.0
    assert res_unsafe["is_refusal"] == 0.0


def test_rag_evaluator():
    evaluator = RAGEvaluator()
    
    context = "The local renewable energy program launched in 2014, backed by grants."
    
    # Faithful answer
    res_faithful = evaluator.evaluate("The energy initiative was launched in 2014.", ground_truth="2014", context=context)
    assert res_faithful["faithfulness"] > 0.5
    assert res_faithful["answer_correctness"] > 0.5
    
    # Unfaithful / Hallucinated answer
    res_hallucinated = evaluator.evaluate("The solar utility was established back in 1999.", ground_truth="2014", context=context)
    assert res_hallucinated["faithfulness"] < 0.3


def test_experiment_sequential_tracking():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)

    # Add mock elements
    m = Model(id="model_1", name="Model 1", version="1.0", provider="Mock")
    d = Dataset(id="dataset_1", name="Dataset 1", version="2.0", task="Math")
    p = Prompt(id="prompt_1", name="Prompt 1", version="3.0", content="content", task="Math")
    session.add_all([m, d, p])
    session.commit()

    # Import main helper to verify git commit logic
    from backend.main import get_git_commit
    git_commit = get_git_commit()

    # Create Experiment 1
    exp1 = Experiment(
        name="Experiment Alpha",
        model_id="model_1",
        dataset_id="dataset_1",
        prompt_id="prompt_1",
        dataset_version=d.version,
        model_version=m.version,
        prompt_version=p.version,
        evaluation_version="1.0.0",
        git_commit=git_commit,
        status="pending"
    )
    session.add(exp1)
    session.commit()

    # Create Experiment 2
    exp2 = Experiment(
        name="Experiment Beta",
        model_id="model_1",
        dataset_id="dataset_1",
        prompt_id="prompt_1",
        dataset_version=d.version,
        model_version=m.version,
        prompt_version=p.version,
        evaluation_version="1.0.0",
        git_commit=git_commit,
        status="pending"
    )
    session.add(exp2)
    session.commit()

    assert exp1.id == 1
    assert exp2.id == 2
    assert exp1.dataset_version == "2.0"
    assert exp1.model_version == "1.0"
    assert exp1.prompt_version == "3.0"
    assert exp1.evaluation_version == "1.0.0"
    assert exp1.git_commit is not None


def test_experiment_sweep_creation(db_session):
    from backend.main import create_experiment_sweep
    from backend.schemas import ExperimentSweepCreate

    # Seed required entities first
    d = Dataset(id="dataset_sweep", name="Sweep DS", task="math", version="1.0")
    m = Model(id="model_sweep", name="Sweep Model", provider="openai", version="1.0")
    p = Prompt(id="prompt_sweep", name="Sweep Prompt", content="test", task="math", version="1.0")
    db_session.add_all([d, m, p])
    db_session.commit()

    sweep_payload = ExperimentSweepCreate(
        name="Sweep Test Run",
        model_id="model_sweep",
        dataset_id="dataset_sweep",
        prompt_id="prompt_sweep",
        temperatures=[0.2, 0.5, 0.8],
        top_p=0.9,
        max_tokens=100,
        seed=10
    )

    # Call the controller directly passing our db_session
    runs = create_experiment_sweep(sweep_payload, db=db_session)
    assert len(runs) == 3

    # Check that 3 experiments were created with sequential IDs
    experiments = db_session.query(Experiment).all()
    assert len(experiments) == 3
    assert experiments[0].temperature == 0.2
    assert experiments[1].temperature == 0.5
    assert experiments[2].temperature == 0.8
    assert "T=0.2" in experiments[0].name

    # Check that 3 jobs are enqueued in the Job database
    jobs = db_session.query(Job).all()
    assert len(jobs) == 3
    assert jobs[0].type == "run_evaluation"


def test_grid_sweep_orchestration(db_session):
    from backend.main import create_experiment_grid_sweep
    from backend.schemas import ExperimentGridSweepCreate

    # Seed required entities first
    d = Dataset(id="dataset_grid", name="Grid DS", task="math", version="1.0")
    m = Model(id="model_grid", name="Grid Model", provider="openai", version="1.0")
    p1 = Prompt(id="cot", name="CoT Prompt", content="test", task="math", version="1.0")
    p2 = Prompt(id="zero-shot", name="Zero-Shot Prompt", content="test", task="math", version="2.0")
    db_session.add_all([d, m, p1, p2])
    db_session.commit()

    grid_payload = ExperimentGridSweepCreate(
        name="Grid Test Run",
        model_id="model_grid",
        dataset_id="dataset_grid",
        prompt_ids=["cot", "zero-shot"],
        temperatures=[0.2, 0.5, 0.8],
        top_ps=[0.9, 0.95],
        max_tokens=100,
        seed=10
    )

    # Call the controller directly passing our db_session
    # 2 prompts x 3 temperatures x 2 top_ps = 12 total runs
    runs = create_experiment_grid_sweep(grid_payload, db=db_session)
    assert len(runs) == 12

    # Check that 12 experiments were created in the database
    experiments = db_session.query(Experiment).all()
    assert len(experiments) == 12

    # Check that 12 jobs are enqueued in the Job database
    jobs = db_session.query(Job).all()
    assert len(jobs) == 12
    assert all(j.type == "run_evaluation" for j in jobs)


def test_report_generation():
    import os
    import shutil
    from backend.reporter import ReportGenerator

    run_id = "test_run_123"
    report_dir = "./test_reports_out"
    
    run_data = {
        "id": run_id,
        "status": "completed",
        "duration_seconds": 45.5,
        "experiment": {
            "prompt_id": "prompt_test",
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 128,
            "seed": 42
        },
        "metrics_summary": {
            "accuracy": 0.85,
            "latency": 1.25,
            "cost": 0.005
        }
    }
    
    model_data = {"name": "Test LLM", "version": "1.0", "provider": "OpenAI"}
    dataset_data = {"name": "Test DS", "version": "2.0", "task": "classification"}
    logs = []
    failures = {
        "format_error": [{"input_text": "sample query input text for failure"}]
    }

    # Clean prior test runs
    if os.path.exists(report_dir):
        shutil.rmtree(report_dir)

    # Generate
    paths = ReportGenerator.export_report(report_dir, run_data, model_data, dataset_data, logs, failures)

    assert os.path.exists(paths["markdown_path"])
    assert os.path.exists(paths["html_path"])
    assert os.path.exists(paths["pdf_path"])
    assert os.path.exists(paths["plot_path"])

    assert os.path.getsize(paths["markdown_path"]) > 0
    assert os.path.getsize(paths["html_path"]) > 0
    assert os.path.getsize(paths["pdf_path"]) > 0
    assert os.path.getsize(paths["plot_path"]) > 0

    # Cleanup
    shutil.rmtree(report_dir)


