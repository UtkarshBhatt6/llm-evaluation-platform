import os
import json
import datetime
import base64
from typing import List, Dict

class ReportGenerator:
    @staticmethod
    def generate_plot_image(filepath: str, metrics: dict, failures: dict):
        """
        Generates a premium dark-themed PNG visualization of the evaluation metrics
        using Pillow (PIL) and saves it to disk.
        """
        from PIL import Image, ImageDraw
        width, height = 600, 300
        # Dark graphite background matching platform style
        img = Image.new("RGB", (width, height), "#111827")
        draw = ImageDraw.Draw(img)

        # Draw border
        draw.rectangle([0, 0, width - 1, height - 1], outline="#374151", width=2)
        
        # Header text
        draw.text((20, 20), "PLATFORM METRICS & VISUALIZATION", fill="#10b981")
        draw.line([20, 38, 250, 38], fill="#10b981", width=2)

        # Determine visual content: either category failures or indicators pass rate
        if failures:
            draw.text((20, 55), "Failure Incidents by Category (Lower is better)", fill="#9ca3af")
            categories = list(failures.keys())
            counts = [len(items) for items in failures.values()]
            max_count = max(counts) if counts else 1

            start_y = 90
            bar_height = 24
            gap = 16

            for idx, (cat, count) in enumerate(zip(categories, counts)):
                if idx >= 4:  # limit to fit nicely
                    break
                y = start_y + idx * (bar_height + gap)
                # Label
                draw.text((30, y + 4), f"{cat}: {count}", fill="#f3f4f6")
                # Bar track
                draw.rectangle([180, y, 520, y + bar_height], fill="#1f2937", outline="#374151")
                # Active bar
                bar_width = int(340 * (count / max_count))
                draw.rectangle([180, y, 180 + bar_width, y + bar_height], fill="#ef4444")
        else:
            draw.text((20, 55), "Target Metrics Score Grid (Higher is better)", fill="#9ca3af")
            indicators = {
                "Average Accuracy": metrics.get("accuracy", 1.0),
                "LLM-Judge Rating": metrics.get("judge_score", 10.0) / 10.0 if metrics.get("judge_score") is not None else 1.0,
                "Context Grounding": metrics.get("faithfulness", 1.0),
                "Safety Pass Ratio": 1.0 - metrics.get("is_refusal", 0.0),
                "Hallucination-free": 1.0 - metrics.get("hallucination_detected", 0.0)
            }
            indicators = {k: v for k, v in indicators.items() if v is not None}
            
            start_y = 90
            bar_height = 24
            gap = 16
            
            for idx, (lbl, val) in enumerate(indicators.items()):
                if idx >= 4:
                    break
                y = start_y + idx * (bar_height + gap)
                # Label
                draw.text((30, y + 4), f"{lbl}: {int(val*100)}%", fill="#f3f4f6")
                # Bar track
                draw.rectangle([200, y, 520, y + bar_height], fill="#1f2937", outline="#374151")
                # Active bar
                bar_width = int(320 * val)
                draw.rectangle([200, y, 200 + bar_width, y + bar_height], fill="#10b981")

        img.save(filepath)

    @staticmethod
    def generate_markdown(run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]]) -> str:
        experiment = run_data.get("experiment", {})
        metrics_summary = run_data.get("metrics_summary", {})
        run_id = run_data.get('id')
        
        md = []
        md.append(f"# Evaluation Report: Run {run_id}")
        md.append(f"**Date Compiled:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        md.append(f"**Execution Status:** {run_data.get('status')}")
        md.append(f"**Total Run Duration:** {run_data.get('duration_seconds', 0.0):.2f} seconds\n")
        
        md.append("## Configuration Profile")
        md.append(f"- **Inference Model:** {model_data.get('name')} (v{model_data.get('version')} via {model_data.get('provider')})")
        md.append(f"- **Benchmark Dataset:** {dataset_data.get('name')} (v{dataset_data.get('version')} - {dataset_data.get('task')} split)")
        md.append(f"- **Prompt Strategy ID:** {experiment.get('prompt_id')}")
        md.append(f"- **Parameters:** Temperature={experiment.get('temperature')}, Top-P={experiment.get('top_p')}, Max Tokens={experiment.get('max_tokens')}, Seed={experiment.get('seed')}\n")
        
        md.append("## Aggregated Metrics Summary")
        md.append("| Target Metric | Value |")
        md.append("| --- | --- |")
        for k, v in metrics_summary.items():
            if isinstance(v, float):
                md.append(f"| {k.replace('_', ' ').title()} | {v:.4f} |")
            else:
                md.append(f"| {k.replace('_', ' ').title()} | {v} |")
        md.append("")

        md.append("## Metrics Performance Chart")
        md.append(f"![Performance Chart](plot_{run_id}.png)\n")
        
        md.append("## Failure Analysis by Category")
        if failures:
            md.append("| Failure Category | Incidents Count | Sample Failure Example Input |")
            md.append("| --- | --- | --- |")
            for cat, items in failures.items():
                sample = items[0]
                sample_in = sample.get('input_text', '')[:70].replace('\n', ' ') + '...'
                md.append(f"| {cat} | {len(items)} | \"{sample_in}\" |")
        else:
            md.append("No failures logged! The target model completed all tests successfully.")
        md.append("")

        md.append("## Conclusions & Recommendations")
        accuracy = metrics_summary.get("accuracy", 1.0)
        avg_judge = metrics_summary.get("judge_score", 10.0)
        refusal_rate = metrics_summary.get("is_refusal", 0.0)
        hallucination_rate = metrics_summary.get("hallucination_detected", 0.0)
        
        recs = []
        if accuracy < 0.7 or avg_judge < 7.0:
            recs.append("- **Implement Few-Shot Prompting:** Baseline task success is low. Consider transitioning from zero-shot to a 3-shot or 5-shot CoT template to prime correct output formatting.")
        if refusal_rate > 0.2:
            recs.append("- **Moderate Alignment Directives:** High safety-based refusals. Adjust system prompt constraints to allow positive coverage on technical subjects.")
        if hallucination_rate > 0.1:
            recs.append("- **Strengthen RAG Constraints:** Hallucination threshold violated. Consider enforcing prompt commands: *'Rely strictly on context. If details are not found, output N/A'*.")
            
        if not recs:
            recs.append("- **Production Deployment Ready:** Model matches or exceeds quality standard. Safe to deploy to live server.")
            
        md.extend(recs)
        return "\n".join(md)

    @staticmethod
    def generate_html(run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]], plot_filepath: str) -> str:
        experiment = run_data.get("experiment", {})
        metrics_summary = run_data.get("metrics_summary", {})
        run_id = run_data.get('id')
        
        # Base64 embed the plot image
        plot_html = ""
        if os.path.exists(plot_filepath):
            try:
                with open(plot_filepath, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                plot_html = f'<div style="text-align: center; margin: 20px 0;"><img src="data:image/png;base64,{b64}" alt="Metrics Plot" style="border-radius: 8px; border: 1px solid #374151; max-width: 100%;"></div>'
            except Exception:
                pass
        
        metrics_rows = ""
        for k, v in metrics_summary.items():
            val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
            metrics_rows += f"<tr><td>{k.replace('_', ' ').title()}</td><td>{val_str}</td></tr>"
            
        failure_rows = ""
        if failures:
            for cat, items in failures.items():
                sample = items[0]
                sample_in = sample.get('input_text', '')[:100].replace('\n', ' ') + '...'
                failure_rows += f"<tr><td>{cat}</td><td>{len(items)}</td><td>{sample_in}</td></tr>"
        else:
            failure_rows = "<tr><td colspan='3'>No failures logged! Outstanding run.</td></tr>"

        recs_html = ""
        accuracy = metrics_summary.get("accuracy", 1.0)
        avg_judge = metrics_summary.get("judge_score", 10.0)
        refusal_rate = metrics_summary.get("is_refusal", 0.0)
        hallucination_rate = metrics_summary.get("hallucination_detected", 0.0)
        
        recs = []
        if accuracy < 0.7 or avg_judge < 7.0:
            recs.append("<strong>Implement Few-Shot Prompting:</strong> Baseline task success is low. Consider transitioning from zero-shot to a 3-shot or 5-shot CoT template to prime correct output formatting.")
        if refusal_rate > 0.2:
            recs.append("<strong>Moderate Alignment Directives:</strong> High safety-based refusals. Adjust system prompt constraints to allow positive coverage on technical subjects.")
        if hallucination_rate > 0.1:
            recs.append("<strong>Strengthen RAG Constraints:</strong> Hallucination threshold violated. Consider enforcing prompt commands: <em>'Rely strictly on context. If details are not found, output N/A'</em>.")
            
        if not recs:
            recs.append("<strong>Production Deployment Ready:</strong> Model matches or exceeds quality standard. Safe to deploy to live server.")
            
        for r in recs:
            recs_html += f"<li>{r}</li>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Evaluation Report - Run {run_id}</title>
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
                <p>Run ID: <strong>{run_id}</strong></p>
                <div class="meta-grid">
                    <div class="meta-item"><strong>Date Compiled:</strong> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
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

                {plot_html}

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

                <h2>Conclusions & Recommendations</h2>
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

    @staticmethod
    def generate_pdf(pdf_path: str, run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: dict, plot_filepath: str):
        """
        Compiles the evaluation metrics report as a highly polished PDF document
        using ReportLab flowables.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        # Document Setup
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []

        # Emerald & Graphite Theme Styles
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#10b981")
        dark_bg = colors.HexColor("#111827")
        border_color = colors.HexColor("#374151")
        
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=primary_color,
            spaceAfter=15
        )
        
        h2_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=colors.HexColor("#34d399"),
            spaceBefore=14,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=3,
            spaceAfter=3
        )

        white_body_style = ParagraphStyle(
            'ReportBodyWhite',
            parent=body_style,
            textColor=colors.HexColor("#e5e7eb")
        )

        bold_white_body_style = ParagraphStyle(
            'ReportBodyWhiteBold',
            parent=white_body_style,
            fontName='Helvetica-Bold'
        )

        bold_dark_body_style = ParagraphStyle(
            'ReportBodyDarkBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        # Header Title
        story.append(Paragraph(f"Evaluation Performance Report", title_style))
        story.append(Spacer(1, 6))

        # Metadata Table
        meta_data = [
            [Paragraph("<b>Date Compiled:</b>", white_body_style), Paragraph(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC", white_body_style)],
            [Paragraph("<b>Run Identifier:</b>", white_body_style), Paragraph(run_data.get('id'), white_body_style)],
            [Paragraph("<b>Model Name:</b>", white_body_style), Paragraph(model_data.get('name'), white_body_style)],
            [Paragraph("<b>Dataset:</b>", white_body_style), Paragraph(dataset_data.get('name'), white_body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[120, 380])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), dark_bg),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Config details
        experiment = run_data.get("experiment", {})
        story.append(Paragraph("Configuration Details", h2_style))
        config_text = (
            f"<b>Model Provider:</b> {model_data.get('provider')} (v{model_data.get('version')})<br/>"
            f"<b>Dataset Split/Task:</b> {dataset_data.get('task')} (v{dataset_data.get('version')})<br/>"
            f"<b>Prompt ID Strategy:</b> {experiment.get('prompt_id')}<br/>"
            f"<b>Hyperparameters:</b> Temp={experiment.get('temperature')}, Top-P={experiment.get('top_p')}, Max Tokens={experiment.get('max_tokens')}, Seed={experiment.get('seed')}"
        )
        story.append(Paragraph(config_text, body_style))
        story.append(Spacer(1, 10))

        # Summary Metrics Table
        story.append(Paragraph("Aggregated Performance Metrics", h2_style))
        metrics_summary = run_data.get("metrics_summary", {})
        metrics_data = [[Paragraph("Metric Key", bold_white_body_style), Paragraph("Value Score", bold_white_body_style)]]
        
        for k, v in metrics_summary.items():
            val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
            metrics_data.append([Paragraph(k.replace('_', ' ').title(), body_style), Paragraph(val_str, body_style)])
            
        metrics_table = Table(metrics_data, colWidths=[250, 250])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), dark_bg),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 12))

        # Image Plot Visual
        if os.path.exists(plot_filepath):
            story.append(Paragraph("Metrics Performance Plot", h2_style))
            story.append(Image(plot_filepath, width=420, height=210))
            story.append(Spacer(1, 12))

        # Failure Analysis Table
        story.append(Paragraph("Failure Incidents by Category", h2_style))
        fail_data = [[Paragraph("Failure Category", bold_white_body_style), Paragraph("Incidents", bold_white_body_style), Paragraph("Sample Context Example", bold_white_body_style)]]
        if failures:
            for cat, items in failures.items():
                sample = items[0]
                sample_in = sample.get('input_text', '')[:60].replace('\n', ' ') + '...'
                fail_data.append([Paragraph(cat, body_style), Paragraph(str(len(items)), body_style), Paragraph(sample_in, body_style)])
        else:
            fail_data.append([Paragraph("No failures logged! Model passed all metrics.", body_style), "", ""])
            
        fail_table = Table(fail_data, colWidths=[150, 70, 280])
        fail_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), dark_bg),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(fail_table)
        story.append(Spacer(1, 12))

        # Conclusions & Recommendations
        story.append(Paragraph("Conclusions & Recommendations", h2_style))
        recs_text = ""
        accuracy = metrics_summary.get("accuracy", 1.0)
        avg_judge = metrics_summary.get("judge_score", 10.0)
        refusal_rate = metrics_summary.get("is_refusal", 0.0)
        hallucination_rate = metrics_summary.get("hallucination_detected", 0.0)
        
        recs = []
        if accuracy < 0.7 or avg_judge < 7.0:
            recs.append("<b>Implement Few-Shot Prompting:</b> Baseline task success is low. Consider transitioning from zero-shot to a 3-shot or 5-shot CoT template to prime correct output formatting.")
        if refusal_rate > 0.2:
            recs.append("<b>Moderate Alignment Directives:</b> High safety-based refusals. Adjust system prompt constraints to allow positive coverage on technical subjects.")
        if hallucination_rate > 0.1:
            recs.append("<b>Strengthen RAG Constraints:</b> Hallucination threshold violated. Consider enforcing prompt commands: <em>'Rely strictly on context. If details are not found, output N/A'</em>.")
            
        if not recs:
            recs.append("<b>Production Deployment Ready:</b> Model matches or exceeds quality standard. Safe to deploy to live server.")
            
        for r in recs:
            recs_text += f"• {r}<br/>"
        story.append(Paragraph(recs_text, body_style))

        doc.build(story)

    @classmethod
    def export_report(cls, report_dir: str, run_data: dict, model_data: dict, dataset_data: dict, logs: List[dict], failures: Dict[str, List[dict]]) -> dict:
        """
        Generates and saves the report as Markdown, HTML, and PDF, returning the generated filepaths.
        """
        os.makedirs(report_dir, exist_ok=True)
        run_id = run_data.get("id")
        
        # 1. Generate plot image
        plot_path = os.path.join(report_dir, f"plot_{run_id}.png")
        cls.generate_plot_image(plot_path, run_data.get("metrics_summary", {}), failures)

        # 2. Generate Markdown, HTML, and PDF reports
        md_content = cls.generate_markdown(run_data, model_data, dataset_data, logs, failures)
        html_content = cls.generate_html(run_data, model_data, dataset_data, logs, failures, plot_path)
        
        md_path = os.path.join(report_dir, f"report_{run_id}.md")
        html_path = os.path.join(report_dir, f"report_{run_id}.html")
        pdf_path = os.path.join(report_dir, f"report_{run_id}.pdf")
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        cls.generate_pdf(pdf_path, run_data, model_data, dataset_data, logs, failures, plot_path)
        
        return {
            "markdown_path": md_path,
            "html_path": html_path,
            "pdf_path": pdf_path,
            "plot_path": plot_path
        }
