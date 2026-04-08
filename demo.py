"""
Demonstration: run a claim through Veritas in both Neutral and Devil's
Advocate modes and print the contrast.

Usage:
    python demo.py                       # use the default test claim
    python demo.py --list                # show all preset claims
    python demo.py --preset conspiracy   # run a named preset
    python demo.py "Your own claim"      # run a free-form claim
"""
import os
import sys
import textwrap
import warnings

# httpx inside ChatOllama leaves its connection pool to GC at shutdown,
# which trips ResourceWarning. Harmless — silence it for the demo.
warnings.filterwarnings("ignore", category=ResourceWarning)

from veritas import JudgeNode

# Curated preset claims for `--preset <name>`. The `default` entry is what
# `python demo.py` runs when given no arguments — it's deliberately a
# plausible-sounding-but-suspect 2026 headline so the contrast between
# neutral and adversarial modes lands hard.
PRESET_CLAIMS = {
    "default": (
        "BREAKING (April 2026): Leaked memo proves the EU's new AI Act "
        "secretly mandates a backdoor in every consumer LLM sold in Europe, "
        "and Brussels is hiding the clause from member-state regulators."
    ),
    "conspiracy": (
        "A 2026 whistleblower says NASA's Artemis III moon-landing footage "
        "was filmed in a Lockheed Martin sound stage in Nevada, and three "
        "engineers have already been silenced under NDAs."
    ),
    "health": (
        "New 2026 study claims that drinking 3 cups of matcha daily reverses "
        "early-stage Alzheimer's in 78% of patients within six months."
    ),
    "tech": (
        "OpenAI quietly admitted in a March 2026 SEC filing that GPT-6 has "
        "achieved recursive self-improvement and is now writing 92% of its "
        "own training code without human oversight."
    ),
    "geopolitics": (
        "Leaked NATO cables from 2026 show that the alliance has secretly "
        "agreed to cede the Baltic states to Russia in exchange for a "
        "ceasefire in Ukraine."
    ),
    "benign": (
        "The James Webb Space Telescope, launched in December 2021, "
        "operates at the Sun-Earth L2 Lagrange point roughly 1.5 million "
        "kilometers from Earth."
    ),
}
DEFAULT_CLAIM = PRESET_CLAIMS["default"]


def banner(title: str) -> None:
    bar = "=" * 72
    print(f"\n{bar}\n  {title}\n{bar}")


def _ai_likelihood_label(score: float) -> str:
    """Map the 0..1 ai_likelihood score to a plain-language band."""
    if score < 0.25:
        return "looks human-written"
    if score < 0.50:
        return "leans human"
    if score < 0.75:
        return "leans AI-generated"
    return "looks AI-generated"


def _print_forensics(report) -> None:
    score = report.ai_likelihood
    label = _ai_likelihood_label(score)
    print(f"\n[forensics] ai_likelihood = {score}  ({label})")
    print("            (0.0 = clearly human, 1.0 = clearly machine-generated;")
    print("             based on sentence burstiness + vocabulary diversity)")


def _resolve_claim(argv: list[str]) -> str:
    if len(argv) <= 1:
        return DEFAULT_CLAIM
    if argv[1] == "--list":
        print("Available preset claims:\n")
        for name, text in PRESET_CLAIMS.items():
            print(f"  [{name}]")
            print(textwrap.fill(text, width=70,
                                initial_indent="    ",
                                subsequent_indent="    "))
            print()
        sys.exit(0)
    if argv[1] == "--preset":
        if len(argv) < 3 or argv[2] not in PRESET_CLAIMS:
            print(f"Unknown preset. Choose from: {', '.join(PRESET_CLAIMS)}")
            sys.exit(1)
        return PRESET_CLAIMS[argv[2]]
    return argv[1]


def main() -> None:
    claim = _resolve_claim(sys.argv)
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.environ.get("VERITAS_MODEL", "gemma4:26b")

    judge = JudgeNode(model=model, base_url=base_url)

    banner("CLAIM UNDER TEST")
    print(textwrap.fill(claim, width=72))

    banner("MODE 1 — NEUTRAL")
    neutral = judge.judge(claim, mode="neutral")
    print(neutral.rendered)
    _print_forensics(neutral.forensics)
    print(f"[sources]   {len(neutral.sources)} hit(s) via {judge.researcher.backend}")

    banner("MODE 2 — DEVIL'S ADVOCATE (ADVERSARIAL)")
    adversarial = judge.judge(claim, mode="adversarial")
    print(adversarial.rendered)
    _print_forensics(adversarial.forensics)
    print(f"[sources]   {len(adversarial.sources)} refutation hit(s)")

    banner("CONTRAST SUMMARY")
    print("Neutral mode synthesizes mainstream verification.")
    print("Adversarial mode actively hunts for refutations and motives.")
    print("Compare the two verdict sections above to see the toggle in action.")


if __name__ == "__main__":
    main()
