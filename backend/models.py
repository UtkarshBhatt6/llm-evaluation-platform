import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True)  # e.g., "gsm8k_v1.2", "mmlu_qa"
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    task = Column(String, nullable=False)  # e.g., "Math", "Coding", "Safety"
    license = Column(String, nullable=True)
    num_samples = Column(Integer, default=0)
    avg_tokens = Column(Integer, default=0)
    splits = Column(JSON, nullable=True)   # list of split names e.g. ["train", "test"]
    metadata_info = Column(JSON, nullable=True)  # mapping of arbitrary metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    experiments = relationship("Experiment", back_populates="dataset")


class Model(Base):
    __tablename__ = "models"
    id = Column(String, primary_key=True)  # e.g., "openai/gpt-4o", "meta/llama3-8b"
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # e.g., "OpenAI", "Gemini", "Anthropic", "Ollama", "HuggingFace", "Mock"
    context_length = Column(Integer, default=4096)
    pricing_input_1k = Column(Float, default=0.0)
    pricing_output_1k = Column(Float, default=0.0)
    latency_avg = Column(Float, default=0.0)  # average latency in seconds
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    experiments = relationship("Experiment", back_populates="model")


class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(String, primary_key=True)  # e.g., "cot_v2", "react_reasoning"
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String, nullable=True)
    task = Column(String, nullable=False)
    variables = Column(JSON, nullable=True)  # list of variables, e.g. ["question", "context"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    experiments = relationship("Experiment", back_populates="prompt")


class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    model_id = Column(String, ForeignKey("models.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    prompt_id = Column(String, ForeignKey("prompts.id"), nullable=False)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.95)
    max_tokens = Column(Integer, default=512)
    seed = Column(Integer, default=42)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    model = relationship("Model", back_populates="experiments")
    dataset = relationship("Dataset", back_populates="experiments")
    prompt = relationship("Prompt", back_populates="experiments")
    evaluation_runs = relationship("EvaluationRun", back_populates="experiment", cascade="all, delete-orphan")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(String, primary_key=True)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)  # progress percentage from 0.0 to 100.0
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    experiment = relationship("Experiment", back_populates="evaluation_runs")
    logs = relationship("EvaluationLog", back_populates="run", cascade="all, delete-orphan")


class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("evaluation_runs.id"), nullable=False)
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)  # Ground truth if available
    generated_output = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)  # JSON dictionary storing individual item metrics
    cost = Column(Float, default=0.0)      # cost of this single completion
    latency = Column(Float, default=0.0)   # generation latency in seconds
    is_failure = Column(Boolean, default=False)
    failure_category = Column(String, nullable=True)  # Math, Reasoning, Long Context, Coding, Formatting, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    run = relationship("EvaluationRun", back_populates="logs")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    queue = Column(String, nullable=False, default="default")
    priority = Column(Integer, nullable=False, default=0)
    deduplication_key = Column(String, nullable=True)
    deduplication_expires_at = Column(DateTime, nullable=True)
    type = Column(String, nullable=False)  # e.g., "run_evaluation"
    payload = Column(JSON, nullable=False)
    state = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed, dead_letter
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    run_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    reserved_until = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
