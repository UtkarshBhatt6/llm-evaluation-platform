# Evaluation Report: Run 6d16abb9-cc7f-4453-9ed5-2d7bc8bab043
**Date:** 2026-07-04 18:54:08 UTC
**Status:** completed
**Duration:** 2.71 seconds

## Configuration
- **Model:** Llama 3 8B (v3.0 via Mock)
- **Dataset:** GSM8K Math (v1.2 - Math task)
- **Prompt Template:** cot_v2
- **Parameters:** Temp=0.7, Top-P=0.95, Max Tokens=256

## Aggregated Metrics Summary
| Metric | Value |
| --- | --- |
| Total Samples | 5 |
| Avg Latency | 0.3469 |
| Total Cost | 0.0010 |
| Accuracy | 0.2000 |
| Bleu | 0.0000 |
| Rouge L | 0.0000 |
| Judge Score | 5.0000 |

## Failure Analysis by Category
| Failure Category | Count | Sample Failure Example |
| --- | --- | --- |
| Math Error | 4 | "Calculate the area of a rectangle with length 15cm and width..." |
| Reasoning (Math) | 1 | "A basket contains 12 apples. If John takes 4 and Sarah takes..." |

## Recommendations
- **Incorporate Few-Shot Examples:** The model's baseline accuracy is low. Try transitioning from zero-shot to a 3-shot or 5-shot prompt template to prime correct output patterns.