from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class DatasetBase(BaseModel):
    id: str = Field(..., description="Unique dataset key, e.g., gsm8k_v1")
    name: str
    version: str
    task: str
    license: Optional[str] = None
    num_samples: int = 0
    avg_tokens: int = 0
    splits: Optional[List[str]] = []
    samples: Optional[List[Dict[str, Any]]] = None
    metadata_info: Optional[Dict[str, Any]] = None

class DatasetResponse(DatasetBase):
    created_at: datetime
    class Config:
        from_attributes = True


class ModelBase(BaseModel):
    id: str = Field(..., description="Unique model key, e.g., openai/gpt-4o")
    name: str
    version: str
    provider: str
    context_length: int = 4096
    pricing_input_1k: float = 0.0
    pricing_output_1k: float = 0.0
    latency_avg: float = 0.0

class ModelResponse(ModelBase):
    created_at: datetime
    class Config:
        from_attributes = True


class PromptBase(BaseModel):
    id: str = Field(..., description="Unique prompt template key, e.g., cot_v2")
    name: str
    version: str
    content: str
    author: Optional[str] = None
    task: str
    variables: Optional[List[str]] = []

class PromptResponse(PromptBase):
    created_at: datetime
    class Config:
        from_attributes = True


class ExperimentCreate(BaseModel):
    name: str
    model_id: str
    dataset_id: str
    prompt_id: str
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 512
    seed: int = 42

class ExperimentSweepCreate(BaseModel):
    name: str
    model_id: str
    dataset_id: str
    prompt_id: str
    temperatures: List[float] = [0.2, 0.4, 0.6, 0.8, 1.0]
    top_p: float = 0.95
    max_tokens: int = 512
    seed: int = 42

class ExperimentGridSweepCreate(BaseModel):
    name: str
    model_id: str
    dataset_id: str
    prompt_ids: List[str]
    temperatures: List[float] = [0.2, 0.5, 0.8]
    top_ps: List[float] = [0.9, 0.95]
    max_tokens: int = 512
    seed: int = 42

class ExperimentResponse(BaseModel):
    id: int
    name: str
    model_id: str
    dataset_id: str
    prompt_id: str
    dataset_version: str
    model_version: str
    prompt_version: str
    evaluation_version: str
    git_commit: Optional[str] = None
    temperature: float
    top_p: float
    max_tokens: int
    seed: int
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class EvaluationRunResponse(BaseModel):
    id: str
    experiment_id: int
    status: str
    error_message: Optional[str] = None
    progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class EvaluationLogResponse(BaseModel):
    id: str
    run_id: str
    input_text: str
    expected_output: Optional[str] = None
    generated_output: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    cost: float
    latency: float
    is_failure: bool
    failure_category: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class RunDetailResponse(BaseModel):
    id: str
    status: str
    progress: float
    experiment: ExperimentResponse
    model: ModelResponse
    dataset: DatasetResponse
    metrics_summary: Dict[str, Any]
    logs: List[EvaluationLogResponse]
    failures: Dict[str, List[Dict[str, Any]]]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStats(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    dead_letter: int


class LeaderboardEntry(BaseModel):
    model_id: str
    model_name: str
    provider: str
    avg_accuracy: float
    avg_judge_score: Optional[float] = 0.0
    avg_latency: float
    avg_cost: float
    total_runs: int
