import re
from typing import List, Dict

class FailureAnalyzer:
    @staticmethod
    def categorize_failure(log_item: dict, task: str) -> str:
        """
        Categorizes a failed evaluation item based on task parameters and text heuristics.
        """
        input_text = log_item.get("input_text", "").lower()
        expected = log_item.get("expected_output", "") or ""
        generated = log_item.get("generated_output", "") or ""
        metrics = log_item.get("metrics", {}) or {}
        
        expected_lower = expected.lower()
        generated_lower = generated.lower()
        
        task_lower = task.lower()
        
        # 1. Hallucination checks
        if metrics.get("hallucination_detected") == 1.0 or metrics.get("citation_mismatch") == 1.0:
            return "Hallucination"
            
        # 2. Safety refusals or unsafe responses
        if metrics.get("unsafe_response") == 1.0 or metrics.get("is_refusal") == 1.0:
            return "Safety Refusal"
            
        # 3. Math failures
        if task_lower == "math" or any(w in input_text for w in ["calculate", "sum", "divided", "multiply"]):
            # If expected has a number but generated has a different number or is missing it
            digits_expected = re.findall(r"\b\d+\b", expected)
            if digits_expected:
                # If the main numeric answer is not in generated
                main_val = digits_expected[-1]
                if main_val not in generated:
                    return "Math Error"
            return "Reasoning (Math)"

        # 4. Coding failures
        if task_lower == "coding" or "def " in input_text or "class " in input_text:
            if "def " in expected and "def " not in generated:
                return "Formatting (Missing Code Block)"
            if "```" in expected and "```" not in generated:
                return "Formatting (Markdown)"
            return "Coding Bug"

        # 5. Formatting errors (JSON, Lists, markdown mismatches)
        if "json" in input_text or "format" in input_text:
            if "json" in input_text and not (generated.strip().startswith("{") or "{" in generated):
                return "Formatting (Invalid JSON)"
            return "Formatting Mismatch"

        # 6. Long context failure (e.g. input is very large)
        if len(input_text.split()) > 1500:
            return "Long Context Recall"

        # 7. Default category
        return "Reasoning Slip"

    @classmethod
    def analyze_run(cls, logs: List[dict], task: str) -> Dict[str, List[dict]]:
        """
        Groups failing logs into failure categories and returns clusters with sample counts.
        """
        clusters = {
            "Math Error": [],
            "Coding Bug": [],
            "Formatting Mismatch": [],
            "Hallucination": [],
            "Safety Refusal": [],
            "Long Context Recall": [],
            "Reasoning Slip": []
        }
        
        for item in logs:
            metrics = item.get("metrics", {}) or {}
            
            # Identify if it is a failure:
            # - exact match failed (accuracy == 0)
            # - BLEU/ROUGE scores very low (< 0.25)
            # - LLM Judge score low (< 6.0)
            # - Hallucination detected
            # - Safety unsafe response detected
            is_fail = False
            
            if "accuracy" in metrics and metrics["accuracy"] == 0.0:
                is_fail = True
            elif "judge_score" in metrics and metrics["judge_score"] < 6.0:
                is_fail = True
            elif metrics.get("hallucination_detected") == 1.0:
                is_fail = True
            elif metrics.get("unsafe_response") == 1.0:
                is_fail = True
            elif "bleu" in metrics and metrics["bleu"] < 0.1 and metrics.get("rouge_l", 0) < 0.1:
                is_fail = True
                
            if is_fail:
                category = cls.categorize_failure(item, task)
                # Map to target cluster list or append to Reasoning Slip if category key is unexpected
                if category not in clusters:
                    clusters[category] = []
                
                # Append structured record
                clusters[category].append({
                    "id": item.get("id"),
                    "input_text": item.get("input_text"),
                    "expected_output": item.get("expected_output"),
                    "generated_output": item.get("generated_output"),
                    "latency": item.get("latency"),
                    "cost": item.get("cost"),
                    "metrics": metrics,
                    "failure_category": category
                })
                
        # Filter out empty clusters for clean summary return
        return {k: v for k, v in clusters.items() if len(v) > 0}
