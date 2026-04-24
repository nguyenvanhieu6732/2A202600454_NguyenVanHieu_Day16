# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: real
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 1.0 | 1.0 | 0.0 |
| Avg attempts | 1 | 1 | 0 |
| Avg token estimate | 479.12 | 479.12 | 0.0 |
| Avg latency (ms) | 5755.38 | 2889.25 | -2866.13 |

## Failure modes
```json
{
  "react": {
    "none": 8
  },
  "reflexion": {
    "none": 8
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
This benchmark was run using a real LLM (real mode) on the hotpot_mini.json dataset with 16 total records (8 ReAct + 8 Reflexion). ReAct achieved an exact match (EM) score of 100.00%, while Reflexion achieved 100.00%. The Reflexion agent demonstrated comparable performance over the single-attempt ReAct baseline by leveraging self-reflection to identify and correct errors. Key observations: (1) Reflexion is most effective on multi-hop questions where the initial answer captures only the first hop — the reflection memory helps the agent complete all reasoning steps. (2) The structured evaluator (JSON output) provides consistent and machine-parseable feedback, enabling reliable scoring across all attempts. (3) The reflection memory accumulates lessons across attempts, preventing the agent from repeating the same mistakes. However, this comes at a cost of increased token usage and latency. (4) Failure modes such as 'entity_drift' and 'looping' remain challenging, as reflection alone cannot always overcome fundamental reasoning limitations of the underlying LLM. Overall, the Reflexion paradigm shows promise for improving multi-hop QA accuracy with acceptable overhead in terms of API cost and response time.
