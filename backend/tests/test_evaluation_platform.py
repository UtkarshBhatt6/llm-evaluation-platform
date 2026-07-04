import datetime
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import backend elements
from backend.db import Base
from backend.models import Job
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
