import os
import json
import datetime
from typing import List, Dict

class ReportGenerator:
    @staticmethod
    def generate_markdown(run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]]) -> str:
        experiment = run_data.get("experiment", {})
        metrics_summary = run_data.get("metrics_summary", {})
        
        md = []
        md.append(f"# Evaluation Report: Run {run_data.get('id')}")
        md.append(f"**Date:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        md.append(f"**Status:** {run_data.get('status')}")
        md.append(f"**Duration:** {run_data.get('duration_seconds', 0.0):.2f} seconds\n")
        
        md.append("## Configuration")
        md.append(f"- **Model:** {model_data.get('name')} (v{model_data.get('version')} via {model_data.get('provider')})")
        md.append(f"- **Dataset:** {dataset_data.get('name')} (v{dataset_data.get('version')} - {dataset_data.get('task')} task)")
        md.append(f"- **Prompt Template:** {experiment.get('prompt_id')}")
        md.append(f"- **Parameters:** Temp={experiment.get('temperature')}, Top-P={experiment.get('top_p')}, Max Tokens={experiment.get('max_tokens')}\n")
        
        md.append("## Aggregated Metrics Summary")
        md.append("| Metric | Value |")
        md.append("| --- | --- |")
        for k, v in metrics_summary.items():
            if isinstance(v, float):
                md.append(f"| {k.replace('_', ' ').title()} | {v:.4f} |")
            else:
                md.append(f"| {k.replace('_', ' ').title()} | {v} |")
        md.append("")
        
        md.append("## Failure Analysis by Category")
        if failures:
            md.append("| Failure Category | Count | Sample Failure Example |")
            md.append("| --- | --- | --- |")
            for cat, items in failures.items():
                sample = items[0]
                sample_in = sample.get('input_text', '')[:60].replace('\n', ' ') + '...'
                md.append(f"| {cat} | {len(items)} | \"{sample_in}\" |")
        else:
            md.append("No failures logged! Perfect execution run.")
        md.append("")

        md.append("## Recommendations")
        # Compute synthetic recommendations based on metrics
        accuracy = metrics_summary.get("accuracy", 1.0)
        avg_judge = metrics_summary.get("judge_score", 10.0)
        refusal_rate = metrics_summary.get("is_refusal", 0.0)
        hallucination_rate = metrics_summary.get("hallucination_detected", 0.0)
        
        recs = []
        if accuracy < 0.7 or avg_judge < 7.0:
            recs.append("- **Incorporate Few-Shot Examples:** The model's baseline accuracy is low. Try transitioning from zero-shot to a 3-shot or 5-shot prompt template to prime correct output patterns.")
        if refusal_rate > 0.2:
            recs.append("- **Tune Refusal Guardrails:** The model shows high refusal rates. Review input queries for false-positive trigger keywords and adjust safety filters or prompt guidelines.")
        if hallucination_rate > 0.1:
            recs.append("- **Refine RAG Context Alignment:** Hallucination rate is high. Consider increasing retrieval chunk overlap or implementing an prompt constraint: *'Answer only based on facts explicitly stated in the context'*. ")
        if metrics_summary.get("bleu", 1.0) < 0.3 and dataset_data.get("task") == "qa":
            recs.append("- **Loosen Exact Comparison Bounds:** Language overlap is low. We recommend shifting to an LLM-as-a-Judge semantic rating rather than exact matching for general QA datasets.")
            
        if not recs:
            recs.append("- **Ready for Deployment:** The model shows solid performance on all monitored criteria. No immediate formatting or template updates needed.")
            
        md.extend(recs)
        
        return "\n".join(md)

    @staticmethod
    def generate_html(run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]]) -> str:
        experiment = run_data.get("experiment", {})
        metrics_summary = run_data.get("metrics_summary", {})
        
        # Build metrics rows
        metrics_rows = ""
        for k, v in metrics_summary.items():
            val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
            metrics_rows += f"<tr><td>{k.replace('_', ' ').title()}</td><td>{val_str}</td></tr>"
            
        # Build failure rows
        failure_rows = ""
        if failures:
            for cat, items in failures.items():
                sample = items[0]
                sample_in = sample.get('input_text', '')[:100].replace('\n', ' ') + '...'
                failure_rows += f"<tr><td>{cat}</td><td>{len(items)}</td><td>{sample_in}</td></tr>"
        else:
            failure_rows = "<tr><td colspan='3'>No failures logged! Outstanding run.</td></tr>"

        # Recommendations list
        recs_html = ""
        accuracy = metrics_summary.get("accuracy", 1.0)
        avg_judge = metrics_summary.get("judge_score", 10.0)
        refusal_rate = metrics_summary.get("is_refusal", 0.0)
        hallucination_rate = metrics_summary.get("hallucination_detected", 0.0)
        
        recs = []
        if accuracy < 0.7 or avg_judge < 7.0:
            recs.append("<strong>Incorporate Few-Shot Examples:</strong> The model's baseline accuracy is low. Try transitioning from zero-shot to a 3-shot or 5-shot prompt template to prime correct output patterns.")
        if refusal_rate > 0.2:
            recs.append("<strong>Tune Refusal Guardrails:</strong> The model shows high refusal rates. Review input queries for false-positive trigger keywords and adjust safety filters or prompt guidelines.")
        if hallucination_rate > 0.1:
            recs.append("<strong>Refine RAG Context Alignment:</strong> Hallucination rate is high. Consider increasing retrieval chunk overlap or implementing an prompt constraint.")
            
        if not recs:
            recs.append("<strong>Ready for Deployment:</strong> The model shows solid performance on all monitored criteria. No immediate formatting or template updates needed.")
            
        for r in recs:
            recs_html += f"<li>{r}</li>"

        # Embedded premium styling in HTML template (emerald/graphite styled report)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Evaluation Report - Run {run_data.get('id')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #111827;
                    color: #e5e7eb;
                    margin: 0;
                    padding: 40px;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background-color: #1f2937;
                    padding: 30px;
                    border-radius: 12px;
                    border: 1px solid #10b981;
                    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.15);
                }}
                h1 {{
                    color: #10b981;
                    border-bottom: 2px solid #374151;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                h2 {{
                    color: #34d399;
                    margin-top: 30px;
                    border-bottom: 1px solid #4b5563;
                    padding-bottom: 5px;
                }}
                .meta-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    background: #111827;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .meta-item {{
                    font-size: 14px;
                }}
                .meta-item strong {{
                    color: #10b981;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #374151;
                }}
                th {{
                    background-color: #111827;
                    color: #34d399;
                }}
                li {{
                    margin-bottom: 10px;
                    line-height: 1.5;
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Evaluation Report</h1>
                <p>Run ID: <strong>{run_data.get('id')}</strong></p>
                <div class="meta-grid">
                    <div class="meta-item"><strong>Date:</strong> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
                    <div class="meta-item"><strong>Run Status:</strong> {run_data.get('status')}</div>
                    <div class="meta-item"><strong>Model Name:</strong> {model_data.get('name')} ({model_data.get('provider')})</div>
                    <div class="meta-item"><strong>Dataset:</strong> {dataset_data.get('name')} ({dataset_data.get('task')})</div>
                </div>

                <h2>Configuration Parameters</h2>
                <div class="meta-grid" style="grid-template-columns: 1fr 1fr 1fr 1fr;">
                    <div class="meta-item"><strong>Temperature:</strong> {experiment.get('temperature')}</div>
                    <div class="meta-item"><strong>Top P:</strong> {experiment.get('top_p')}</div>
                    <div class="meta-item"><strong>Max Tokens:</strong> {experiment.get('max_tokens')}</div>
                    <div class="meta-item"><strong>Seed:</strong> {experiment.get('seed')}</div>
                </div>

                <h2>Summary Metrics</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics_rows}
                    </tbody>
                </table>

                <h2>Failures by Category</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Count</th>
                            <th>Example Sample</th>
                        </tr>
                    </thead>
                    <tbody>
                        {failure_rows}
                    </tbody>
                </table>

                <h2>Recommendations</h2>
                <ul>
                    {recs_html}
                </ul>

                <div class="footer">
                    Generated automatically by Generic ML Experimentation and Evaluation Platform.
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @classmethod
    def export_report(cls, report_dir: str, run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]]) -> dict:
        """
        Generates and saves the report as Markdown and HTML, returning the generated filepaths.
        """
        os.makedirs(report_dir, exist_ok=True)
        run_id = run_data.get("id")
        
        md_content = cls.generate_markdown(run_data, model_data, dataset_data, logs, failures)
        html_content = cls.generate_html(run_data, model_data, dataset_data, logs, failures)
        
        md_path = os.path.join(report_dir, f"report_{run_id}.md")
        html_path = os.path.join(report_dir, f"report_{run_id}.html")
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return {
            "markdown_path": md_path,
            "html_path": html_path
        }
