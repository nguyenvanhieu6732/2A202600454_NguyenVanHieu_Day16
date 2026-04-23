from __future__ import annotations
import json
import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

load_dotenv()

# Khởi tạo OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _extract_json(text: str) -> dict:
    """Trích xuất JSON từ phản hồi của LLM, xử lý cả trường hợp có markdown code block."""
    text = text.strip()
    # Thử tìm JSON trong markdown code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    # Thử tìm JSON object trực tiếp
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _build_actor_prompt(example: QAExample, reflection_memory: list[str]) -> str:
    """Xây dựng prompt cho Actor dựa trên câu hỏi, context và bộ nhớ reflection."""
    context_str = "\n\n".join(
        f"[{chunk.title}]: {chunk.text}" for chunk in example.context
    )
    prompt = f"Question: {example.question}\n\nContext:\n{context_str}"
    if reflection_memory:
        lessons = "\n".join(f"- {r}" for r in reflection_memory)
        prompt += f"\n\nPrevious reflection lessons (avoid these mistakes):\n{lessons}"
    return prompt


def actor_answer(
    example: QAExample,
    attempt_id: int,
    agent_type: str,
    reflection_memory: list[str],
) -> tuple[str, int, int]:
    """
    Gọi LLM để lấy câu trả lời cho câu hỏi.
    Returns: (answer, total_tokens, latency_ms)
    """
    user_prompt = _build_actor_prompt(example, reflection_memory)
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": ACTOR_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=100,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    answer = response.choices[0].message.content.strip()
    total_tokens = response.usage.total_tokens if response.usage else 0
    return answer, total_tokens, latency_ms


def evaluator(
    example: QAExample, answer: str
) -> tuple[JudgeResult, int, int]:
    """
    Gọi LLM để đánh giá câu trả lời.
    Returns: (JudgeResult, total_tokens, latency_ms)
    """
    user_prompt = (
        f"Question: {example.question}\n"
        f"Gold answer: {example.gold_answer}\n"
        f"Predicted answer: {answer}"
    )
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=300,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    total_tokens = response.usage.total_tokens if response.usage else 0
    raw = response.choices[0].message.content.strip()
    try:
        data = _extract_json(raw)
        result = JudgeResult(**data)
    except Exception:
        # Fallback: nếu LLM không trả JSON đúng, dùng string matching
        from .utils import normalize_answer
        is_correct = normalize_answer(example.gold_answer) == normalize_answer(answer)
        result = JudgeResult(
            score=1 if is_correct else 0,
            reason=raw[:200] if raw else "Could not parse evaluator response",
        )
    return result, total_tokens, latency_ms


def reflector(
    example: QAExample, attempt_id: int, judge: JudgeResult, answer: str
) -> tuple[ReflectionEntry, int, int]:
    """
    Gọi LLM để phân tích lỗi và đưa ra chiến thuật mới.
    Returns: (ReflectionEntry, total_tokens, latency_ms)
    """
    context_str = "\n".join(
        f"[{chunk.title}]: {chunk.text}" for chunk in example.context
    )
    user_prompt = (
        f"Question: {example.question}\n"
        f"Context:\n{context_str}\n"
        f"Wrong answer: {answer}\n"
        f"Evaluation: {judge.reason}\n"
        f"Missing evidence: {judge.missing_evidence}"
    )
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=400,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    total_tokens = response.usage.total_tokens if response.usage else 0
    raw = response.choices[0].message.content.strip()
    try:
        data = _extract_json(raw)
        entry = ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=data.get("failure_reason", ""),
            lesson=data.get("lesson", ""),
            next_strategy=data.get("next_strategy", ""),
        )
    except Exception:
        entry = ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson="Could not parse reflector output",
            next_strategy="Try again with more careful reasoning",
        )
    return entry, total_tokens, latency_ms
