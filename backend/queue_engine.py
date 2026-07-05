import datetime
import json
import logging
import random
import threading
import time
from typing import Callable, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import Job

logger = logging.getLogger("queue_engine")
logger.setLevel(logging.INFO)
# Simple console handler
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class RetryPolicy:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0, multiplier: float = 2.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def calculate_backoff(self, retries: int) -> float:
        delay = self.base_delay * (self.multiplier ** retries)
        if delay > self.max_delay:
            delay = self.max_delay
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)  # 50% to 100% of delay
        return delay


class QueueEngine:
    """Manages queue actions like enqueue, dequeue, ack, nack, heartbeat, and sweep."""
    
    @staticmethod
    def enqueue(db: Session, job_id: str, job_type: str, payload: dict, queue: str = "default", priority: int = 0, deduplication_key: str = None, deduplication_expires_at: datetime.datetime = None, max_retries: int = 3, run_at: datetime.datetime = None) -> bool:
        now = datetime.datetime.utcnow()
        if not run_at:
            run_at = now

        # Deduplication check
        if deduplication_key:
            duplicate = db.query(Job).filter(
                Job.deduplication_key == deduplication_key,
                (Job.state != "completed") | (Job.deduplication_expires_at > now)
            ).first()
            if duplicate:
                logger.info(f"Deduplicated job with key: {deduplication_key}")
                return False

        job = Job(
            id=job_id,
            queue=queue,
            priority=priority,
            deduplication_key=deduplication_key,
            deduplication_expires_at=deduplication_expires_at,
            type=job_type,
            payload=payload,
            state="pending",
            retries=0,
            max_retries=max_retries,
            run_at=run_at,
            created_at=now,
            updated_at=now
        )
        db.add(job)
        db.commit()
        return True

    @staticmethod
    def dequeue_batch(session_factory, queues: List[str], types: List[str], batch_size: int, lease_duration: datetime.timedelta) -> List[dict]:
        """Claims jobs using optimistic transaction locking similar to Go implementation."""
        for attempt in range(5):
            db = session_factory()
            try:
                now = datetime.datetime.utcnow()
                # Query candidates
                query = db.query(Job).filter(
                    Job.state.in_(["pending", "failed"]),
                    Job.run_at <= now
                )
                if queues:
                    query = query.filter(Job.queue.in_(queues))
                if types:
                    query = query.filter(Job.type.in_(types))

                candidates = query.order_by(Job.priority.desc(), Job.run_at.asc(), Job.created_at.asc()).limit(batch_size).all()
                
                if not candidates:
                    db.close()
                    return []

                claimed = []
                reserved_until = now + lease_duration

                for job in candidates:
                    # Concurrency-safe atomic check and update
                    rows = db.query(Job).filter(
                        Job.id == job.id,
                        Job.state.in_(["pending", "failed"])
                    ).update({
                        "state": "processing",
                        "reserved_until": reserved_until,
                        "updated_at": now
                    }, synchronize_session=False)

                    if rows == 1:
                        # Copy data to avoid SQLAlchemy bound session issues
                        claimed.append({
                            "id": job.id,
                            "queue": job.queue,
                            "priority": job.priority,
                            "type": job.type,
                            "payload": job.payload,
                            "retries": job.retries,
                            "max_retries": job.max_retries,
                            "run_at": job.run_at,
                            "reserved_until": reserved_until
                        })

                if claimed:
                    db.commit()
                    return claimed
                
                db.rollback()
            except Exception as e:
                db.rollback()
                if "no such table" in str(e).lower():
                    logger.debug("Queue table 'jobs' is not yet initialized. Retrying on next poll.")
                else:
                    logger.error(f"Error in dequeue transaction: {e}")
            finally:
                db.close()
            time.sleep(0.01)  # 10ms backoff
        return []

    @staticmethod
    def ack(session_factory, job_id: str) -> bool:
        db = session_factory()
        try:
            now = datetime.datetime.utcnow()
            rows = db.query(Job).filter(
                Job.id == job_id,
                Job.state == "processing"
            ).update({
                "state": "completed",
                "reserved_until": None,
                "updated_at": now
            }, synchronize_session=False)
            db.commit()
            return rows == 1
        except Exception as e:
            db.rollback()
            logger.error(f"Error in ack: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def nack(session_factory, job_id: str, next_run_in: datetime.timedelta, error: Exception, retry_policy: RetryPolicy) -> bool:
        db = session_factory()
        try:
            now = datetime.datetime.utcnow()
            job = db.query(Job).filter(Job.id == job_id, Job.state == "processing").first()
            if not job:
                return False

            new_retries = job.retries + 1
            if new_retries > job.max_retries:
                job.state = "dead_letter"
                job.reserved_until = None
                job.run_at = datetime.datetime.min  # Never run again
            else:
                job.state = "failed"
                job.retries = new_retries
                job.reserved_until = None
                job.run_at = now + next_run_in

            job.last_error = str(error)
            job.updated_at = now
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error in nack: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def heartbeat(session_factory, job_id: str, extend_by: datetime.timedelta) -> bool:
        db = session_factory()
        try:
            now = datetime.datetime.utcnow()
            new_reserved_until = now + extend_by
            rows = db.query(Job).filter(
                Job.id == job_id,
                Job.state == "processing"
            ).update({
                "reserved_until": new_reserved_until,
                "updated_at": now
            }, synchronize_session=False)
            db.commit()
            return rows == 1
        except Exception as e:
            db.rollback()
            logger.error(f"Error in heartbeat: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def sweep_expired(session_factory) -> int:
        """Finds processing jobs whose reserved_until is past, and marks them failed or DLQ."""
        db = session_factory()
        try:
            now = datetime.datetime.utcnow()
            expired = db.query(Job).filter(
                Job.state == "processing",
                Job.reserved_until < now
            ).all()

            if not expired:
                return 0

            count = 0
            for job in expired:
                new_retries = job.retries + 1
                if new_retries > job.max_retries:
                    state = "dead_letter"
                    run_at = datetime.datetime.min
                else:
                    state = "failed"
                    run_at = now + datetime.timedelta(seconds=5)  # Quick retry for timeouts

                # Claim and update
                rows = db.query(Job).filter(
                    Job.id == job.id,
                    Job.state == "processing",
                    Job.reserved_until < now
                ).update({
                    "state": state,
                    "retries": new_retries,
                    "last_error": "lease expired: worker heartbeat timeout",
                    "reserved_until": None,
                    "run_at": run_at,
                    "updated_at": now
                }, synchronize_session=False)
                if rows > 0:
                    count += 1
            
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Error in sweep_expired: {e}")
            return 0
        finally:
            db.close()


class WorkerPool:
    """Orchestrates job workers in separate threads and runs the lease sweeper."""
    
    def __init__(self, session_factory, concurrency: int = 3, queues: List[str] = None, poll_interval: float = 0.2, lease_duration: float = 15.0, sweeper_interval: float = 3.0, retry_policy: RetryPolicy = None, on_state_change: Callable = None):
        self.session_factory = session_factory
        self.concurrency = concurrency
        self.queues = queues or ["default"]
        self.poll_interval = poll_interval
        self.lease_duration = datetime.timedelta(seconds=lease_duration)
        self.sweeper_interval = sweeper_interval
        self.retry_policy = retry_policy or RetryPolicy()
        self.on_state_change = on_state_change

        self.handlers: Dict[str, Callable] = {}
        self.active_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def register(self, job_type: str, handler: Callable):
        with self._lock:
            self.handlers[job_type] = handler

    def start(self):
        self._stop_event.clear()
        
        # Start workers
        for i in range(self.concurrency):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            t.start()
            self.active_threads.append(t)

        # Start sweeper
        t_sweep = threading.Thread(target=self._sweeper_loop, daemon=True)
        t_sweep.start()
        self.active_threads.append(t_sweep)

        logger.info(f"WorkerPool started with {self.concurrency} threads. Listening to queues: {self.queues}")

    def stop(self):
        logger.info("Stopping WorkerPool, waiting for workers to drain...")
        self._stop_event.set()
        for t in self.active_threads:
            if t.is_alive():
                t.join(timeout=2.0)
        self.active_threads.clear()
        logger.info("WorkerPool stopped successfully")

    def _worker_loop(self, worker_id: int):
        while not self._stop_event.is_set():
            with self._lock:
                types = list(self.handlers.keys())

            if not types:
                time.sleep(self.poll_interval)
                continue

            # Poll/Dequeue a single job
            jobs = QueueEngine.dequeue_batch(
                self.session_factory, 
                self.queues, 
                types, 
                batch_size=1, 
                lease_duration=self.lease_duration
            )

            if not jobs:
                time.sleep(self.poll_interval)
                continue

            job = jobs[0]
            if self.on_state_change:
                self.on_state_change()

            self._process_job(worker_id, job)

    def _process_job(self, worker_id: int, job: dict):
        job_id = job["id"]
        job_type = job["type"]
        retries = job["retries"]
        max_retries = job["max_retries"]

        logger.info(f"[Worker {worker_id}] ==> Processing Job {job_id} [Type: {job_type}, Retry: {retries}/{max_retries}]")
        
        with self._lock:
            handler = self.handlers.get(job_type)

        if not handler:
            logger.error(f"[Worker {worker_id}] No handler registered for job type {job_type}")
            return

        # Setup custom heartbeat function context
        def run_heartbeat(extend_seconds: float = 15.0):
            extend_by = datetime.timedelta(seconds=extend_seconds)
            return QueueEngine.heartbeat(self.session_factory, job_id, extend_by)

        start_time = time.time()
        try:
            # Execute worker handler passing payload and heartbeat hook
            handler(job["payload"], heartbeat_fn=run_heartbeat)
            
            duration = time.time() - start_time
            logger.info(f"[Worker {worker_id}] Job {job_id} completed successfully in {duration:.3f}s")
            
            QueueEngine.ack(self.session_factory, job_id)
        except Exception as err:
            duration = time.time() - start_time
            logger.error(f"[Worker {worker_id}] Job {job_id} failed: {err}")
            
            backoff_secs = self.retry_policy.calculate_backoff(retries)
            next_run_in = datetime.timedelta(seconds=backoff_secs)
            QueueEngine.nack(self.session_factory, job_id, next_run_in, err, self.retry_policy)

        if self.on_state_change:
            self.on_state_change()

    def _sweeper_loop(self):
        while not self._stop_event.is_set():
            try:
                count = QueueEngine.sweep_expired(self.session_factory)
                if count > 0:
                    logger.info(f"[Sweeper] Released {count} expired job leases")
                    if self.on_state_change:
                        self.on_state_change()
            except Exception as e:
                if "no such table" in str(e).lower():
                    logger.debug("[Sweeper] Jobs table is not yet initialized. Skipping sweep.")
                else:
                    logger.error(f"[Sweeper] Error in sweeping loop: {e}")
            
            # Sleep in increments checking for stop events
            for _ in range(int(self.sweeper_interval * 10)):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)
