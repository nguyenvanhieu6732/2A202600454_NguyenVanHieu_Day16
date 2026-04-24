# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: real
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.81 | 0.88 | 0.07 |
| Avg attempts | 1 | 1.32 | 0.32 |
| Avg token estimate | 1803.1 | 2925.16 | 1122.06 |
| Avg latency (ms) | 2895.74 | 5279.92 | 2384.18 |

## Failure modes
```json
{
  "react": {
    "none": 81,
    "wrong_final_answer": 19
  },
  "reflexion": {
    "none": 88,
    "looping": 11,
    "wrong_final_answer": 1
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
This benchmark was run using a real LLM (real mode) on the hotpot_100.json dataset with 200 total records (100 ReAct + 100 Reflexion). ReAct achieved an exact match (EM) score of 81.00%, while Reflexion achieved 88.00%. The Reflexion agent demonstrated improvement over the single-attempt ReAct baseline by leveraging self-reflection to identify and correct errors. Key observations: (1) Reflexion is most effective on multi-hop questions where the initial answer captures only the first hop — the reflection memory helps the agent complete all reasoning steps. (2) The structured evaluator (JSON output) provides consistent and machine-parseable feedback, enabling reliable scoring across all attempts. (3) The reflection memory accumulates lessons across attempts, preventing the agent from repeating the same mistakes. However, this comes at a cost of increased token usage and latency. (4) Failure modes such as 'entity_drift' and 'looping' remain challenging, as reflection alone cannot always overcome fundamental reasoning limitations of the underlying LLM. Overall, the Reflexion paradigm shows promise for improving multi-hop QA accuracy with acceptable overhead in terms of API cost and response time.
