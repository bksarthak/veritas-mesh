"""
Forensic AI-detection module.

Combines two signals:
  1. Semantic burstiness — humans write in uneven, bursty rhythms (long
     sentences next to short ones, vocabulary spikes). LLM output tends to
     regress toward a smoother, lower-variance mean.
  2. Gemma 4 pattern analysis — asks the local Gemma 4 model to look for
     telltale generation artifacts (hedging stock phrases, scaffolding
     transitions, uniform paragraph shapes).

Both signals are returned independently so the JudgeNode can weight them.
"""
from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass, asdict
from typing import Optional

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:  # pragma: no cover - optional at import time
    ChatOllama = None  # type: ignore
    SystemMessage = HumanMessage = None  # type: ignore


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"\b\w+\b")


@dataclass
class BurstinessReport:
    sentence_count: int
    mean_sentence_len: float
    stdev_sentence_len: float
    burstiness: float          # stdev / mean (higher = more human-like)
    type_token_ratio: float    # vocabulary diversity
    ai_likelihood: float       # 0.0 (human) .. 1.0 (AI)
    pattern_notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ForensicsAnalyzer:
    """Statistical + LLM-assisted AI-text detector."""

    # Empirical thresholds — burstiness < 0.45 is unusually smooth.
    _SMOOTH_THRESHOLD = 0.45
    _LOW_DIVERSITY_THRESHOLD = 0.55

    def __init__(
        self,
        model: str = "gemma4:26b",
        base_url: str = "http://127.0.0.1:11434",
        use_llm: bool = True,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.use_llm = use_llm and ChatOllama is not None
        self._llm = None
        if self.use_llm:
            self._llm = ChatOllama(
                model=model,
                base_url=base_url,
                temperature=0.2,
                num_ctx=8192,
            )

    # ---------- statistical pass ----------

    def _burstiness(self, text: str) -> tuple[float, float, float, int]:
        sentences = [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
        if len(sentences) < 2:
            return 0.0, 0.0, 0.0, len(sentences)
        lens = [len(_WORD.findall(s)) for s in sentences]
        mean = statistics.fmean(lens)
        stdev = statistics.pstdev(lens)
        burst = (stdev / mean) if mean else 0.0
        return mean, stdev, burst, len(sentences)

    def _ttr(self, text: str) -> float:
        words = [w.lower() for w in _WORD.findall(text)]
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    # ---------- LLM pass ----------

    def _pattern_check(self, text: str) -> Optional[str]:
        if not self._llm:
            return None
        sys = SystemMessage(content=(
            "You are a forensic linguist specializing in detecting machine-"
            "generated text. Look for: stock hedging phrases, uniform "
            "paragraph shapes, scaffolding transitions ('Furthermore', 'In "
            "conclusion'), absence of idiosyncratic voice. Respond with "
            "1-3 short bullet points."
        ))
        usr = HumanMessage(content=f"Analyze this text:\n\n{text[:4000]}")
        try:
            resp = self._llm.invoke([sys, usr])
            return resp.content.strip() if hasattr(resp, "content") else str(resp)
        except Exception as exc:  # pragma: no cover
            return f"(pattern check unavailable: {exc})"

    # ---------- public ----------

    def analyze(self, text: str) -> BurstinessReport:
        mean, stdev, burst, n = self._burstiness(text)
        ttr = self._ttr(text)

        # Score: smoother + lower diversity => more AI-like.
        smoothness_score = max(0.0, 1.0 - (burst / self._SMOOTH_THRESHOLD))
        diversity_score = max(0.0, 1.0 - (ttr / self._LOW_DIVERSITY_THRESHOLD))
        ai_likelihood = min(1.0, 0.6 * smoothness_score + 0.4 * diversity_score)
        # Smooth via sigmoid for nicer 0..1 spread.
        ai_likelihood = 1 / (1 + math.exp(-6 * (ai_likelihood - 0.5)))

        notes = self._pattern_check(text) if self.use_llm else None

        return BurstinessReport(
            sentence_count=n,
            mean_sentence_len=round(mean, 2),
            stdev_sentence_len=round(stdev, 2),
            burstiness=round(burst, 3),
            type_token_ratio=round(ttr, 3),
            ai_likelihood=round(ai_likelihood, 3),
            pattern_notes=notes,
        )
