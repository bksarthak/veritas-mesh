# 🔍 Veritas-Mesh

### *Two AIs walk into a fact-check. They disagree. You decide.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Ollama](https://img.shields.io/badge/built%20with-Ollama-black)](https://ollama.com)
[![Local-only](https://img.shields.io/badge/cloud-not%20required-brightgreen)](#)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> Run any tweet, headline, or news story through **two adversarial AI judges** —
> one neutral, one assuming you're being lied to — and watch them disagree in
> real time. Runs entirely on your own hardware. No cloud. No accounts. No
> trust required.

---

## ⚡ See it in action

![Veritas-Mesh: neutral vs adversarial verdicts on the same claim](docs/demo.png)

*Above: the same conspiracy claim run through both modes. The neutral judge
summarizes the consensus; the Devil's Advocate hunts for refutations and
alternative motives. **The contrast is the product.***

Try it yourself in 30 seconds:

```bash
python demo.py --preset conspiracy   # Artemis III moon-hoax claim
python demo.py --preset health       # matcha / Alzheimer's claim
python demo.py --preset benign       # known-true sanity check
python demo.py "Your own claim"      # free-form
```

Veritas doesn't tell you what's true. It shows you the strongest case *for*
the claim and the strongest case *against* the claim, side by side, and
lets you make the call.

---

## 🤔 Why this exists

Modern fact-checking is broken in three specific ways, and Veritas-Mesh is a
direct response to each:

1. **Centralized fact-checkers are politically captured.** Whether you trust
   Snopes, Reuters, Ground News, or none of them depends entirely on your
   priors. A tool that runs on *your* hardware and shows its work is the
   only way out of that loop.
2. **Single-model AI verdicts launder bias.** Asking one LLM "is this true?"
   collapses a complex question into one model's training-data priors.
   Veritas runs the same claim through two adversarial framings so you can
   see where the model agrees with itself and where it doesn't.
3. **You can't trust an AI to grade itself.** The Devil's Advocate mode is
   built on the assumption that the LLM is wrong by default — and asks it
   to prove its own neutral verdict wrong. The disagreement *is* the signal.

---

## 🏆 How it compares

|                                  | Veritas-Mesh | GPTZero | Snopes | Ground News | ChatGPT |
|----------------------------------|:------------:|:-------:|:------:|:-----------:|:-------:|
| Runs locally (no cloud)          |      ✅      |    ❌   |   ❌   |      ❌     |    ❌   |
| Open source                      |      ✅      |    ❌   |   ❌   |      ❌     |    ❌   |
| AI-text detection                |      ✅      |    ✅   |   ❌   |      ❌     |    ❌   |
| Adversarial Devil's-Advocate mode|      ✅      |    ❌   |   ❌   |      ❌     |    ❌   |
| Shows source snippets            |      ✅      |    ❌   |   ✅   |      ✅     |    ❌   |
| No signup / no API key required  |      ✅      |    ❌   |   ✅   |      ❌     |    ❌   |
| Editorial bias                   |     None     |   N/A   |  Some  |    Curated  |  Some   |

---

## 🖥️ Hardware Compatibility

Veritas-Mesh **scales automatically from 8 GB to 24 GB+ VRAM**. The bundled
setup script reads `nvidia-smi` and pulls the best-fitting Gemma 4 variant:

| VRAM    | Variant       | Notes |
|---------|---------------|-------|
| < 9 GB  | `gemma4:2b`   | Edge / mobile / Raspberry Pi-class |
| < 14 GB | `gemma4:9b`   | Most consumer GPUs |
| < 22 GB | `gemma4:12b`  | Mid-tier prosumer |
| ≥ 22 GB | `gemma4:26b`  | Full SOTA MoE (25.2B / 3.8B active) |

No GPU? Ollama will fall back to CPU automatically. Slower (~30–90s per
verdict instead of ~5s) but it works.

---

## 📋 Prerequisites

1. **Python 3.10 or newer** — `python3 --version`
2. **[Ollama](https://ollama.com/download)** — the local LLM runtime that
   actually runs Gemma 4. After installing:
   ```bash
   ollama --version
   curl http://127.0.0.1:11434/api/tags   # should return JSON
   ```
3. **A Gemma 4 model.** Pick from the table above; for most users:
   ```bash
   ollama pull gemma4:9b
   ```

**Optional:** A free [Tavily](https://tavily.com) API key for better web
search. Without it, Veritas falls back to DuckDuckGo (free, no signup,
flakier rate-limits). With Tavily, set `export TAVILY_API_KEY=tvly-...`
before running.

---

## ⚡ Quick Start

### Local (recommended)

```bash
git clone https://github.com/<you>/veritas-mesh.git
cd veritas-mesh
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python demo.py                     # default claim
python demo.py --preset benign     # known-true claim (sanity check)
python demo.py --preset conspiracy # known-false claim (the fun one)
python demo.py "Your own claim"    # free-form
```

### Docker

```bash
export TAVILY_API_KEY=tvly-...     # optional
docker compose up --build
```

`docker-compose.yml` defines two hardened services:

- **`ollama-provider`** — Ollama with NVIDIA GPU passthrough, bound to
  `127.0.0.1` only. Auto-pulls the optimal Gemma 4 variant on first boot.
- **`veritas-app`** — the Python app, running as an unprivileged user with
  `read_only`, `cap_drop: [ALL]`, and `no-new-privileges`.

---

## 🎛️ The Adversarial Toggle

| Mode | Behavior |
|------|----------|
| `neutral` | Summarizes consensus, lists mainstream verification, assigns a confidence band. |
| `adversarial` | *Devil's Advocate.* Prompt: **"Assume this post is a calculated lie. Find the logical inconsistencies and alternative motives."** Searches specifically for refuting evidence. |

Both modes return the same `Verdict` object so you can compare them side by
side. The contrast is the actual product.

---

## 🧠 Architecture

```
veritas/
├── forensics.py    # Semantic burstiness + Gemma 4 pattern analysis
├── researcher.py   # Tavily / DuckDuckGo source retrieval
├── judge.py        # JudgeNode — neutral vs adversarial reasoning toggle
└── __init__.py
```

- **`forensics.py`** — measures sentence-length burstiness, type/token ratio,
  and (optionally) asks Gemma 4 to look for telltale generation artifacts.
  Returns an `ai_likelihood` score in `[0, 1]`, where **0.0 = clearly
  human-written** and **1.0 = clearly machine-generated**. Demo prints a
  plain-language band — *looks human-written / leans human / leans
  AI-generated / looks AI-generated*.
- **`researcher.py`** — pluggable web search. Prefers Tavily if
  `TAVILY_API_KEY` is set, otherwise falls back to DuckDuckGo. Exposes
  `search()` and `search_refutations()` (the adversarial query that biases
  the engine toward debunks and fact-checks).
- **`judge.py`** — the reasoning engine. The `JudgeNode` accepts a `mode`
  flag and routes the claim through one of two prompts. Both prompts are
  hardened against prompt-injection via tagged data blocks and a sanitizer.

---

## 🐛 Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `httpx.ConnectError: Connection refused` to `127.0.0.1:11434` | Ollama isn't running | Start it: `ollama serve` (or `systemctl status ollama` on Linux) |
| `model "gemma4:9b" not found` | Model not pulled yet | `ollama pull gemma4:9b` |
| `[sources] 0 hit(s) via duckduckgo` | DuckDuckGo rate-limited you | Wait a few minutes, or get a free Tavily key |
| Verdict says "UNVERIFIED (LLM unavailable)" | The judge couldn't reach Ollama or the model timed out | Check Ollama is running and the model is pulled; first run is slow as the model loads into VRAM |
| Very slow first run | Cold model load | Normal — subsequent runs reuse the loaded model |
| `RuntimeWarning: duckduckgo_search has been renamed to ddgs` | Old package installed | `pip install ddgs` and uninstall `duckduckgo-search` |

Verbose logging:
```bash
PYTHONUNBUFFERED=1 python -u demo.py 2>&1 | tee veritas-debug.log
```

---

## 🚧 Known Gaps & Limitations

Veritas-Mesh is a working prototype, not a finished product. **These are the
highest-leverage places to contribute** — pick a number, open a PR.

| # | Gap | Why it matters | Potential fix |
|---|-----|----------------|---------------|
| 1 | **Forensics is statistical, not semantic.** Burstiness + TTR catch lazy LLM output but a human writer with smooth prose will score "AI-like", and an attacker can prompt an LLM to *write burstily* and defeat it. | High false-positive and false-negative rates on adversarial inputs. The score is a hint, not proof. | Add a model-fingerprint detector (Binoculars, GPTZero-style log-likelihood ratios) as a second signal, and ensemble the two. |
| 2 | **No URL fetching.** Veritas only sees the search-result snippet, not the page. | Verdicts are only as good as the snippet quality. | Add an opt-in fetcher with `httpx` + `trafilatura`, with SSRF protection (block private IPs, `file://`, etc). |
| 3 | **DuckDuckGo backend is unreliable.** | Default install often produces `0 hit(s)` runs that look like bugs. | Add Brave Search API and SerpAPI; document Tavily as the recommended default; consider self-hosted SearXNG. |
| 4 | **Single-LLM judge.** | The "Devil's Advocate" mode isn't truly adversarial — it's the same model role-playing. | Wire in a second model (Llama 3.1, Mistral) for the adversarial pass. |
| 5 | **No source credibility weighting.** | Easy to bias verdicts by spamming low-quality sources. | Domain-reputation tiering (Reuters/AP > newspapers > blogs > forums). |
| 6 | **No claim decomposition.** | A claim that's 90% true and 10% false gets flattened. | Pre-process compound claims into atomic sub-claims and judge each. |
| 7 | **English-only in practice.** | Non-English claims return degraded verdicts. | Detect language with `langdetect`/`fasttext`, localize prompts. |
| 8 | **No persistence / no audit log.** | Can't review history, can't track drift. | SQLite ledger of `(timestamp, claim, mode, verdict, sources, model)`. |
| 9 | **Prompt-injection defense is best-effort.** | A clever attacker who controls a top search result can still influence verdicts via tone/framing. | "Second opinion" pass: re-evaluate verdict with sources stripped, flag divergence. |
| 10 | **No tests.** | Refactors are risky. | Unit tests for `_sanitize_untrusted`, deterministic burstiness fixtures, mocked end-to-end tests. |

#1 and #2 have the biggest effect on **verdict quality**. #9 and #10 have the
biggest effect on **trustworthiness**. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🛡️ Security

Veritas-Mesh has been reviewed for prompt injection, exception leakage,
container hardening, and SSRF. Highlights:

- All untrusted content (claims, web snippets) is sanitized and wrapped in
  tagged data blocks the LLM is instructed to treat as data, not commands.
- Exception text is logged locally but **never** rendered into the verdict
  (HTTP errors can include API keys).
- The Docker container runs as an unprivileged user with `read_only: true`,
  `cap_drop: [ALL]`, `no-new-privileges`, and Ollama bound to localhost.
- No `subprocess`, no `shell=True`, no filesystem writes, no URL fetching —
  the attack surface is intentionally tiny.

Found a security issue? Open a private security advisory on GitHub rather
than a public issue.

---

## 🤖 AI Attribution

**Built by a human and an AI assistant (Claude) in collaboration, in 2026.**

This is a feature, not a confession. An AI-truthfulness tool that hides the
fact that AI helped build it would be a joke. Every line of code in this
repo was reviewed by a human before commit, and every prompt was tuned
against real-world claims. The collaboration model is the same one we
recommend for using Veritas itself: don't trust the AI, but don't dismiss
it either — read what it says and decide.

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=bksarthak/veritas-mesh&type=Date)](https://star-history.com/#bksarthak/veritas-mesh&Date)

*Replace `bksarthak` after forking.*

---

## 📜 License

[MIT](LICENSE) — do whatever you want, just don't blame us.

---

## 🧭 Design Principles

- **Local-only by default.** No claim, no source snippet, and no verdict ever
  leaves your machine unless you explicitly configure an external search API.
- **Both sides of the mirror.** Veritas does not tell you what is true. It
  shows you the strongest case for and the strongest case against, and lets
  you decide.
- **Transparent provenance.** AI-assisted, AI-built, AI-powered — and we say
  so on the box.
