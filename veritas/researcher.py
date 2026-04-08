"""
Web research module — pulls supporting AND conflicting sources for a claim.

Backends (auto-selected by available API key / package):
  1. Tavily        — preferred, requires TAVILY_API_KEY
  2. DuckDuckGo    — fallback via `duckduckgo_search` (no key)

The Researcher exposes two operations:
  - search(query)            : neutral query
  - search_refutations(claim): adversarial query that explicitly seeks
                               contradicting evidence
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class SourceHit:
    title: str
    url: str
    snippet: str
    backend: str

    def to_dict(self) -> dict:
        return asdict(self)


class Researcher:
    def __init__(self, max_results: int = 6) -> None:
        self.max_results = max_results
        self.backend = self._pick_backend()

    def _pick_backend(self) -> str:
        if os.environ.get("TAVILY_API_KEY"):
            try:
                import tavily  # noqa: F401
                return "tavily"
            except ImportError:
                pass
        try:
            import ddgs  # noqa: F401
            return "duckduckgo"
        except ImportError:
            try:
                import duckduckgo_search  # noqa: F401
                return "duckduckgo"
            except ImportError:
                return "none"

    # ------------- public -------------

    def search(self, query: str) -> List[SourceHit]:
        return self._dispatch(query)

    def search_refutations(self, claim: str) -> List[SourceHit]:
        # Adversarial query phrasing — bias the search engine toward debunks.
        # Strip embedded double-quotes from the claim so we don't break the
        # phrase-quoting around it (and so a crafted claim can't inject
        # extra search operators).
        safe_claim = claim.replace('"', " ").strip()
        # Cap query length — most search backends silently truncate long
        # queries, but an unbounded one is also a cost/abuse vector.
        if len(safe_claim) > 400:
            safe_claim = safe_claim[:400]
        adv_query = (
            f'"{safe_claim}" debunked OR false OR misleading OR fact-check OR hoax'
        )
        return self._dispatch(adv_query)

    # ------------- backends -------------

    def _dispatch(self, query: str) -> List[SourceHit]:
        if self.backend == "tavily":
            return self._tavily(query)
        if self.backend == "duckduckgo":
            return self._ddg(query)
        return []

    def _tavily(self, query: str) -> List[SourceHit]:
        from tavily import TavilyClient
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return []
        client = TavilyClient(api_key=api_key)
        resp = client.search(query=query, max_results=self.max_results,
                             search_depth="advanced")
        out: List[SourceHit] = []
        for r in resp.get("results", []):
            out.append(SourceHit(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", "")[:500],
                backend="tavily",
            ))
        return out

    def _ddg(self, query: str) -> List[SourceHit]:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore
        out: List[SourceHit] = []
        with DDGS() as client:
            for r in client.text(query, max_results=self.max_results):
                out.append(SourceHit(
                    title=r.get("title", ""),
                    url=r.get("href", "") or r.get("url", ""),
                    snippet=(r.get("body", "") or "")[:500],
                    backend="duckduckgo",
                ))
        return out
