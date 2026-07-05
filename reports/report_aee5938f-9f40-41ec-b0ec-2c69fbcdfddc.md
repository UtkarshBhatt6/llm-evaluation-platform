# Evaluation Report: Run aee5938f-9f40-41ec-b0ec-2c69fbcdfddc
**Date Compiled:** 2026-07-05 09:56:24 UTC
**Execution Status:** completed
**Total Run Duration:** 1.06 seconds

## Configuration Profile
- **Inference Model:** Llama 3 8B (v3.0 via Mock)
- **Benchmark Dataset:** HellaSwag (v1.1 - Reasoning split)
- **Prompt Strategy ID:** zero_shot
- **Parameters:** Temperature=0.1, Top-P=0.9, Max Tokens=512, Seed=42

## Aggregated Metrics Summary
| Target Metric | Value |
| --- | --- |
| Total Samples | 3 |
| Avg Latency | 0.3463 |
| Total Cost | 0.0003 |
| Accuracy | 0.0000 |

## Metrics Performance Chart
![Performance Chart](plot_aee5938f-9f40-41ec-b0ec-2c69fbcdfddc.png)

## Failure Analysis by Category
| Failure Category | Incidents Count | Sample Failure Example Input |
| --- | --- | --- |
| Reasoning Slip | 3 | "What is the capital city of France?..." |

## Conclusions & Recommendations
- **Implement Few-Shot Prompting:** Baseline task success is low. Consider transitioning from zero-shot to a 3-shot or 5-shot CoT template to prime correct output formatting.